"""Regression cases from the multi-source date/metadata incident."""
import importlib.util
import json
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("source_app", Path(__file__).parents[1] / "app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


def programme(title, hour=11, rank=220, source=None):
    return {"title": title, "start": f"2026-10-04T{hour:02}:00:00+02:00",
            "end": f"2026-10-04T{hour + 1:02}:00:00+02:00", "_source_rank": rank,
            "_source": source, "desc": "", "subtitle": "", "category": "", "icon": None}


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.store = app.EPGStore.__new__(app.EPGStore)

    def test_navigation_and_calendar_dates_are_not_broadcasts(self):
        parsed = self.store._parse_schedule_lines([
            "4.10.2026", "Jetzt", "20:15", "Vormittags 05:30 - 14:00 Uhr",
            "00:00", "01:00", "02:00 (A)", "02:00 (B)", "03:00",
            "05:30 Uhr", "Tierdetektive", "Seit 11:00 Uhr", "Helene, die wahre Braut",
            "12:00 Uhr", "Tagesschau",
        ], date(2026, 10, 4))
        self.assertEqual([p['title'] for p in parsed], ['Tierdetektive', 'Helene, die wahre Braut', 'Tagesschau'])
        self.assertTrue(all(p['start'].startswith('2026-10-04') for p in parsed))

    def test_unrelated_slot_does_not_inherit_description(self):
        preferred = programme('Helene, die wahre Braut')
        other = programme('Und wer nimmt den Hund?', rank=100)
        other.update(desc='A longer description belonging to another movie', subtitle='Wrong subtitle', icon='wrong.png')
        merged = self.store._merge_program_lists([preferred], [other])
        self.assertEqual(merged[0]['title'], preferred['title'])
        self.assertEqual(merged[0]['desc'], '')
        self.assertEqual(merged[0]['subtitle'], '')
        self.assertIsNone(merged[0]['icon'])

    def test_matching_broadcast_still_gets_metadata(self):
        a = programme('Tagesschau')
        b = programme('Tagesschau', rank=100)
        b['desc'] = 'Matching description'
        self.assertEqual(self.store._merge_program_lists([a], [b])[0]['desc'], b['desc'])

    def test_ard_uses_absolute_dates_and_exact_channel(self):
        def broadcast(name, day, title):
            return {'channel': {'name': name}, 'broadcastedOn': f'2026-10-{day}T11:00:00+02:00',
                    'broadcastEnd': f'2026-10-{day}T12:00:00+02:00', 'coreTitle': title}
        page = '<div>20:15 Uhr</div><script id="preloadedState" type="application/json">' + json.dumps({
            'broadcasts': [broadcast('Das Erste', '04', 'Helene, die wahre Braut'),
                           broadcast('Das Erste', '05', 'Tomorrow'), broadcast('3sat', '04', 'Other channel')]
        }) + '</script>'
        parsed = self.store._parse_ard_programmes(page, 'Das Erste', date(2026, 10, 4))
        self.assertEqual([p['title'] for p in parsed], ['Helene, die wahre Braut'])
        self.assertEqual(parsed[0]['end'], '2026-10-04T12:00:00+02:00')
        self.assertEqual(self.store._parse_ard_programmes(page, 'ZDF', date(2026, 10, 4)), [])

    def test_wrong_page_date_is_rejected(self):
        self.assertFalse(self.store._page_matches_date(['Das Erste: So 04.10.2026', '05.10.2026'], date(2026, 10, 5)))
        self.assertFalse(self.store._page_matches_date(['Heute', '11:00 Sendung'], date(2026, 10, 4)))
        self.assertTrue(self.store._page_matches_date(['Das Erste: So 04.10.2026'], date(2026, 10, 4)))

    def test_sr_ignores_hour_grid_and_keeps_published_dates_and_duration(self):
        page = '<div>00:00</div><div>01:00</div><div>02:00 (A)</div>' + (
            '<li data-pg-show-start="2026-10-04T20:15:00+02:00" data-pg-show-duration="45">'
            '<a title="Wildes Italien">20:15 Wildes Italien</a></li>')
        self.store._fetch_html = lambda url, label: page
        clock = unittest.mock.Mock(wraps=datetime)
        clock.now.return_value = datetime(2026, 10, 4, 12, tzinfo=app.EPG_TIMEZONE)
        with patch.object(app, 'datetime', clock):
            parsed = self.store._fetch_sr_programs()
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]['start'], '2026-10-04T20:15:00+02:00')
        self.assertEqual(parsed[0]['end'], '2026-10-04T21:00:00+02:00')

    def test_broadcast_times_follow_berlin_summer_and_winter_time(self):
        summer = self.store._parse_schedule_lines(['20:15 Film'], date(2026, 7, 4))[0]
        winter = self.store._parse_schedule_lines(['20:15 Film'], date(2026, 12, 4))[0]
        self.assertEqual(summer['start'], '2026-07-04T20:15:00+02:00')
        self.assertEqual(winter['start'], '2026-12-04T20:15:00+01:00')
        self.assertEqual(app.xmltv_datetime('20261004231500 +0000').isoformat(), '2026-10-05T01:15:00+02:00')

    def test_consensus_quarantines_misdated_fallback_but_preserves_missing_channels(self):
        sets = []
        for url, rank, wrong in [(app.OPEN_EPG_URL, 220, False), (app.EPGSHARE_EPG_URL, 210, False), (app.EPGPW_EPG_URL, 100, True)]:
            sets.append([{'id': 'ard', 'available': True, 'programs': [
                programme(('Wrong ' if wrong else 'Correct ') + str(hour), hour, rank, url) for hour in range(8, 13)
            ]}])
        missing = {'id': 'missing', 'available': True, 'programs': [programme('Exclusive', source=app.EPGPW_EPG_URL)]}
        sets[-1].append(missing)
        self.assertEqual(self.store._quarantine_conflicting_fallback(sets), ['ard'])
        self.assertEqual(sets[-1][0]['programs'], [])
        self.assertTrue(missing['programs'])

    def test_cache_freshness_checks_content_instead_of_file_age(self):
        now = datetime.now().astimezone()
        self.store.cache_schema_current = True
        self.store.source_metrics = [{'ok': True}]
        self.store.options = {'refresh_minutes': 180}
        self.store.channels = [{'programs': [{'start': (now - timedelta(days=3)).isoformat(), 'end': (now - timedelta(days=2)).isoformat()}]}]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'parsed.json'
            path.write_text('{}')
            with patch.object(app, 'PARSED_CACHE_FILE', path):
                self.assertFalse(self.store._cache_fresh())
                self.store.channels[0]['programs'] = [{'start': (now - timedelta(minutes=10)).isoformat(), 'end': (now + timedelta(minutes=10)).isoformat()}]
                self.assertTrue(self.store._cache_fresh())
                path.write_text(json.dumps({'schema_version': 5, 'channels': self.store.channels}))
                self.assertFalse(self.store._load_parsed_cache())


if __name__ == '__main__':
    unittest.main()
