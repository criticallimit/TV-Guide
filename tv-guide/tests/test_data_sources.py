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
app = app.backend


def programme(title, hour=11, rank=220, source=None):
    return {"title": title, "start": f"2026-10-04T{hour:02}:00:00+02:00",
            "end": f"2026-10-04T{hour + 1:02}:00:00+02:00", "_source_rank": rank,
            "_source": source, "desc": "", "subtitle": "", "category": "", "icon": None}


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.store = app.EPGStore.__new__(app.EPGStore)

    def test_successful_requests_are_quiet_but_errors_remain_logged(self):
        handler = app.Handler.__new__(app.Handler)
        handler.requestline = 'GET /api/guide HTTP/1.1'
        with patch('builtins.print') as output:
            for status in [200, 201, 204, 302, 304, '200']:
                handler.log_request(status)
            output.assert_not_called()
            for status in [400, 404, 500]:
                handler.log_request(status)
            self.assertEqual(output.call_count, 3)
            handler.log_error('Connection failed: %s', 'test')
            self.assertIn('Connection failed: test', output.call_args.args)

    def test_invalid_xmltv_dates_do_not_break_a_valid_feed(self):
        for value in ['20260230090000 +0100', '20261004100000 +0260',
                      '20261004100000 +2500', '20261004100000 junk', '202610041']:
            self.assertIsNone(app.xmltv_datetime(value), value)
        xml = '''<tv><channel id="ard"><display-name>Das Erste</display-name></channel>
        <programme channel="ard" start="20260230090000 +0100" stop="20260230100000 +0100"><title>Invalid date</title></programme>
        <programme channel="ard" start="20301004120000 +0200" stop="20301004110000 +0200"><title>Reversed times</title></programme>
        <programme channel="ard" start="20301004100000 +0200" stop="20301004110000 +0200"><title>Valid programme</title></programme></tv>'''
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'feed.xml'
            source.write_text(xml, encoding='utf-8')
            with patch.object(self.store, '_open_xml', side_effect=lambda: source.open('rb')):
                channels = self.store._parse()
        self.assertEqual([p['title'] for ch in channels for p in ch['programs']], ['Valid programme'])

    def test_notification_time_is_german_local_time(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit):
                return b''

        reminder = dict(id='test', channel='Das Erste', title='Sendung', start='2030-07-01T18:15:00+00:00')
        with patch.dict(app.os.environ, {'SUPERVISOR_TOKEN': 'test'}), \
             patch.object(app, 'load_options', return_value={'notification_service': 'persistent_notification.create'}), \
             patch.object(app, 'urlopen', return_value=Response()) as send:
            app._ha_notification(reminder)
        self.assertIn('20:15 Uhr', json.loads(send.call_args.args[0].data)['message'])

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

    def test_broadcaster_wins_even_against_higher_numeric_rank(self):
        official = programme('Senderangabe', rank=10, source='official')
        community = programme('Andere Angabe', rank=99999, source='xmltv')
        community['start'] = '2026-10-04T10:45:00+02:00'
        community['end'] = '2026-10-04T12:30:00+02:00'
        for existing, incoming in [([official], [community]), ([community], [official])]:
            self.assertEqual(self.store._merge_program_lists(existing, incoming), [official])

    def test_community_cannot_replace_broadcaster_metadata_or_times(self):
        official = programme('Tagesschau', rank=10, source='official')
        official['desc'] = 'Offizielle Beschreibung'
        community = programme('Tagesschau', rank=99999, source='xmltv')
        community.update(desc='Lange fremde Beschreibung ' * 20, subtitle='Fremde Zusatzangabe', end='2026-10-04T13:00:00+02:00')
        self.assertEqual(self.store._merge_program_lists([community], [official]), [official])
        gap = programme('Spätere Sendung', hour=14, source='xmltv')
        self.assertEqual(len(self.store._merge_program_lists([official], [gap])), 2)

    def test_rtl_page_data_requires_exact_broadcaster_date_and_absolute_times(self):
        records = [dict(name='Film', startDate='2026-10-04T08:50Z', endDate='2026-10-04T10:50Z', broadcastService='RTL'),
                   dict(name='Anderer Sender', startDate='2026-10-04T08:50Z', endDate='2026-10-04T10:50Z', broadcastService='VOX'),
                   dict(name='Falscher Tag', startDate='2026-10-05T08:50Z', endDate='2026-10-05T10:50Z', broadcastService='RTL')]
        flight = '5:' + json.dumps({'broadcasts': records}) + '\n'
        midpoint = len(flight) // 2
        page = ''.join('<script>self.__next_f.push([1,' + json.dumps(chunk) + '])</script>' for chunk in [flight[:midpoint], flight[midpoint:]])
        parsed = self.store._parse_rtl_programmes(page, 'rtl', date(2026, 10, 4))
        self.assertEqual([p['title'] for p in parsed], ['Film'])
        self.assertEqual(parsed[0]['start'], '2026-10-04T10:50:00+02:00')
        self.assertEqual(parsed[0]['end'], '2026-10-04T12:50:00+02:00')

    def test_broadcaster_data_is_loaded_when_all_xml_sources_fail(self):
        store = app.EPGStore()
        store._candidate_urls = lambda: [app.OPEN_EPG_URL]
        store._download = unittest.mock.Mock(side_effect=OSError('XMLTV unavailable'))
        def supplement(channels):
            channels[0]['programs'] = [programme('Offizielle Sendung', source='official')]
            channels[0]['available'] = True
            return channels
        store._supplement_missing_channels = supplement
        store._save_parsed_cache = unittest.mock.Mock()
        store.refresh(force=True)
        self.assertEqual(store.channels[0]['programs'][0]['title'], 'Offizielle Sendung')
        self.assertIsNone(store.last_error)
        store._save_parsed_cache.assert_called_once()

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

    def test_teletext_date_without_year_requires_matching_weekday(self):
        self.assertTrue(self.store._teletext_matches_date(['Sonntag, 4. Oktober', '11:00 Sendung'], date(2026, 10, 4)))
        self.assertFalse(self.store._teletext_matches_date(['Donnerstag, 1. Oktober'], date(2026, 10, 4)))
        self.assertFalse(self.store._teletext_matches_date(['Samstag, 4. Oktober'], date(2026, 10, 4)))
        self.assertFalse(self.store._teletext_matches_date(['Heute', '11:00 Sendung'], date(2026, 10, 4)))

    def test_teletext_accessibility_and_page_references_are_not_titles(self):
        for raw, expected in [('Tagesschau UT', 'Tagesschau'), ('Film AD/UT', 'Film'),
                              ('Sendung UT DGS 305', 'Sendung'), ('Apollo 13 UT 306', 'Apollo 13'),
                              ('Film 300 UT', 'Film 300'), ('Sendung Seite 312', 'Sendung'),
                              ('Die 305', 'Die 305'), ('UT im Titel', 'UT im Titel')]:
            self.assertEqual(self.store._clean_teletext_title(raw), expected)
        page = '''<h1>Sonntag, 4. Oktober</h1>
          <p><a href="305.html">05:30 Morgenmagazin <span>UT</span> <span>305</span></a></p>
          <p>12:00 Film 300 <a href="/mobil/306">306</a> UT</p>
          <p><a href="/mobil/307">13:00 Apollo 13 AD/UT 307</a></p>
          <p>14:00 Die 305</p>'''
        self.store._fetch_html = lambda url, label: page
        clock = unittest.mock.Mock(wraps=datetime)
        clock.now.return_value = datetime(2026, 10, 4, 12, tzinfo=app.EPG_TIMEZONE)
        with patch.object(app, 'datetime', clock), patch.dict(app.TELETEXT_PROVIDER_BY_CHANNEL, {'test': {'today': ['https://example.com/301.html']}}):
            parsed = self.store._fetch_teletext_programs('test')
        self.assertEqual([p['title'] for p in parsed], ['Morgenmagazin', 'Film 300', 'Apollo 13', 'Die 305'])

    def test_official_provider_registry_routes_all_specialized_kinds_without_channel_branches(self):
        calls = []

        def record(name):
            def handler(*args):
                calls.append((name, args))
                return [name]
            return handler

        self.store._fetch_french_programs = record("french")
        self.store._fetch_country_official_programs = record("country")
        self.store._fetch_radio_bremen_programs = record("radiobremen")
        self.store._fetch_swr_programs = record("swr")
        self.store._fetch_sr_programs = record("sr")
        self.store._fetch_generic_official_programs = record("generic")

        expected = {
            "fr_m6": "french", "fr_tf1": "french", "fr_ftv": "french", "fr_arte": "french",
            "srg": "country", "orf": "country", "play": "country", "npo": "country",
            "vrt": "country", "vtm": "country", "nrk": "country", "tv2no": "country",
            "svt": "country",
            "radiobremen": "radiobremen", "swr": "swr", "sr": "sr",
        }
        for kind, handler_name in expected.items():
            provider = {"kind": kind, "marker": "test"}
            self.assertEqual(self.store._fetch_official_programs("channel", provider), [handler_name])

        self.assertEqual(
            self.store._fetch_official_programs("channel", {"kind": "unknown"}),
            ["generic"],
        )
        self.assertEqual(set(self.store.OFFICIAL_PROVIDER_HANDLERS), set(expected))

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
