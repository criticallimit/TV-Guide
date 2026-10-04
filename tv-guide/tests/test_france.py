"""French station identity, dates, titles, logo coverage and exclusions."""
import gzip
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('france_app', Path(__file__).parents[1] / 'app.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
app = app.backend


class FranceTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        root = Path(folder.name)
        paths = patch.multiple(app, OPTIONS_FILE=root / 'options.json', CACHE_FILE=root / 'epg.gz',
                               PARSED_CACHE_FILE=root / 'parsed.json', CHANNEL_PREFS_FILE=root / 'order.json')
        paths.start()
        self.addCleanup(paths.stop)
        self.store = app.EPGStore('fr')
        self.day = datetime.now(app.EPG_TIMEZONE).date()

    def test_country_catalogue_has_24_unique_stations_and_two_bundled_logos(self):
        channels = self.store.catalog['channels']
        self.assertEqual(len(channels), 24)
        self.assertEqual(len({c['id'] for c in channels}), 24)
        for channel in channels:
            self.assertTrue(channel['xmltv_id_only'])
            for key in ['logo_file', 'logo_file_light']:
                self.assertTrue((app.WWW / channel[key]).is_file(), channel['name'])
        self.assertEqual(app.COUNTRIES['fr']['timezone'], 'Europe/Paris')
        with patch.object(app, 'load_options', return_value={'country': 'fr'}), patch.object(app, 'home_assistant_locale', return_value={}):
            self.assertEqual(app.effective_language(), 'fr')

    def test_bfmtv_is_excluded_from_main_and_unmatched_feed_channels(self):
        data = '<tv><channel id="BFMTV.fr"><display-name>BFM TV</display-name></channel>'
        data += '<channel id="TF1.fr"><display-name>TF1</display-name></channel>'
        data += '<channel id="France3Alpes.fr"><display-name>France 3 Alpes</display-name></channel></tv>'
        self.store.cache_file.write_bytes(gzip.compress(data.encode()))
        mapped = self.store._build_channel_map()
        self.assertNotIn('BFMTV.fr', {item['xmltv_id'] for item in mapped.values()})
        self.assertEqual(mapped['fr_tf1']['xmltv_id'], 'TF1.fr')
        self.assertNotIn('fr_france3', mapped, 'A regional channel must not impersonate national France 3')

    def test_bfmtv_cannot_return_from_a_saved_country_cache(self):
        now = datetime.now(app.EPG_TIMEZONE)
        rows = [{'title': 'Current', 'start': now.isoformat(), 'end': (now+timedelta(hours=1)).isoformat()}]
        self.store.channels[0].update(available=True, programs=rows)
        self.store.channels.append({'id': 'cached_bfmtv', 'name': 'BFMTV', 'source_id': 'BFMTV.fr',
                                    'xmltv_ids': ['BFMTV.fr'], 'available': True, 'programs': rows})
        self.store._save_parsed_cache('test')
        restored = app.EPGStore('fr')
        self.assertNotIn('cached_bfmtv', {c['id'] for c in restored.channels})
        self.assertEqual(restored.channels[0]['programs'][0]['title'], 'Current')

    def m6_page(self, rows, marker='M6', day=None):
        state = {'epg': {'programByDateByChannel': {marker: {str(day or self.day): rows}}}}
        return 'root.__dehydratedState = ' + json.dumps({'__reduxState': json.dumps(state)}) + ';'

    def test_m6_preserves_series_episode_planned_times_and_midnight(self):
        row = {'channel': {'code': 'M6'}, 'program': {'title': 'Main series'}, 'title': 'Video episode',
               'subtitle': 'Episode subtitle', 'diffusion_start_date': str(self.day) + ' 23:15:00',
               'diffusion_end_date': str(self.day + timedelta(days=1)) + ' 00:25:00',
               'real_diffusion_start_date': str(self.day) + ' 23:12:27'}
        result = self.store._french_m6(self.m6_page([row]), 'M6', self.day)
        self.assertEqual(result[0]['title'], 'Main series')
        self.assertEqual(result[0]['subtitle'], 'Episode subtitle')
        self.assertEqual(result[0]['start_dt'].hour, 23)
        self.assertEqual(result[0]['start_dt'].minute, 15)
        self.assertEqual(result[0]['end_dt'].date(), self.day + timedelta(days=1))
        self.assertEqual(result[0]['start_dt'].tzinfo.key, 'Europe/Paris')

    def test_m6_rejects_other_station_old_dates_and_inverted_intervals(self):
        row = {'channel': {'code': 'W9'}, 'title': 'Wrong station',
               'diffusion_start_date': str(self.day) + ' 12:00:00', 'diffusion_end_date': str(self.day) + ' 13:00:00'}
        self.assertEqual(self.store._french_m6(self.m6_page([row]), 'M6', self.day), [])
        row['channel']['code'] = 'M6'
        self.assertEqual(self.store._french_m6(self.m6_page([row], day=self.day-timedelta(days=5)), 'M6', self.day), [])
        row['diffusion_end_date'] = str(self.day) + ' 11:00:00'
        self.assertEqual(self.store._french_m6(self.m6_page([row]), 'M6', self.day), [])

    def test_m6_preserves_an_explicit_source_offset(self):
        start = str(self.day) + 'T19:15:00+00:00'
        row = {'channel': {'code': 'M6'}, 'title': 'Programme',
               'diffusion_start_date': start, 'diffusion_end_date': str(self.day) + 'T20:15:00+00:00'}
        result = self.store._french_m6(self.m6_page([row]), 'M6', self.day)
        self.assertEqual(result[0]['start_dt'], datetime.fromisoformat(start))

    def test_ftv_fetches_the_next_week_when_first_grid_has_only_today(self):
        provider = app.COUNTRIES['fr']['providers']['fr_france2']
        start = datetime.now(app.EPG_TIMEZONE).replace(hour=10, minute=0, second=0, microsecond=0)
        def grid(page, marker):
            offset = int(page)
            return [{'title': 'Morning', 'start_dt': start+timedelta(days=offset)},
                    {'title': 'Next', 'start_dt': start+timedelta(days=offset, hours=1)}]
        with patch.object(self.store, '_fetch_html', side_effect=['0', '1', '2']) as fetch, patch.object(self.store, '_french_ftv', side_effect=grid):
            rows = self.store._fetch_french_programs(provider)
        self.assertEqual(fetch.call_count, 3)
        self.assertEqual({datetime.fromisoformat(r['start']).date() for r in rows},
                         {self.day+timedelta(days=n) for n in range(3)})

    def test_tf1_scopes_now_next_evening_to_exact_station(self):
        def row(title, hour):
            return {'title': title, 'startAt': f'{self.day}T{hour}:00:00Z',
                    'endAt': f'{self.day}T{hour}:30:00Z', 'decoration': {'programLabel': 'Series'}}
        data = [{'slug': 'tmc', 'live': row('Wrong', '10')},
                {'slug': 'tf1', 'live': row('Episode', '10'), 'next': row('Next', '11'), 'tonight': row('Evening', '19')}]
        text = '1:' + json.dumps(data) + '\n'
        page = '<script>self.__next_f.push(' + json.dumps([1, text]) + ')</script>'
        result = self.store._french_tf1(page, 'tf1')
        self.assertEqual(len(result), 3)
        self.assertEqual([r['subtitle'] for r in result], ['Episode', 'Next', 'Evening'])
        self.assertTrue(all(r['title'] == 'Series' for r in result))

    def test_ftv_uses_exact_canonical_station_and_deduplicates_featured_rows(self):
        row = f'<time datetime="{self.day}T18:00:00Z">20.00</time><a class="program-item__name">Journal &amp; culture</a>'
        page = '<link rel="canonical" href="https://www.francetvpro.fr/grille/france-2/04-10-2026"/>' + row + row
        self.assertEqual(len(self.store._french_ftv(page, 'france-2')), 1)
        self.assertEqual(self.store._french_ftv(page, 'france-2')[0]['title'], 'Journal & culture')
        self.assertEqual(self.store._french_ftv(page, 'france-3'), [])

    def test_arte_rolls_midnight_to_following_day_and_keeps_subtitle(self):
        def card(time, title):
            return f'<li data-testid="tsguide-itm"><span>{time}</span><h3 data-testid="ts-tsTitle">{title}</h3><p data-testid="ts-tsSubtitle">Episode</p></li>'
        page = f'<link rel="canonical" href="https://www.arte.tv/fr/guide/{self.day:%Y%m%d}/"/>' + card('23:35', 'Evening') + card('01:05', 'Night')
        rows = self.store._french_arte(page, self.day)
        self.assertEqual(rows[1]['start_dt'].date(), self.day + timedelta(days=1))
        self.assertEqual(rows[0]['subtitle'], 'Episode')
        self.assertEqual(self.store._french_arte(page, self.day + timedelta(days=1)), [])
        wrong = page.replace(f'{self.day:%Y%m%d}', '20000101') + f'<a href="https://www.arte.tv/fr/guide/{self.day:%Y%m%d}/">Today</a>'
        self.assertEqual(self.store._french_arte(wrong, self.day), [])

    def test_grid_does_not_invent_last_end_or_bridge_large_gap(self):
        provider = app.COUNTRIES['fr']['providers']['fr_france2']
        start = datetime.now(app.EPG_TIMEZONE).replace(hour=0, minute=0, second=0, microsecond=0)
        rows = [{'title': 'First', 'start_dt': start}, {'title': 'Last', 'start_dt': start+timedelta(hours=20)}]
        with patch.object(self.store, '_fetch_html', return_value='fixture'), patch.object(self.store, '_french_ftv', return_value=rows):
            self.assertEqual(self.store._fetch_french_programs(provider), [])

    def test_french_sources_reject_stale_day_without_harming_feed(self):
        provider = app.COUNTRIES['fr']['providers']['fr_tf1']
        start = datetime.now(app.EPG_TIMEZONE)-timedelta(days=7)
        rows = [{'title': 'Old', 'start_dt': start, 'end_dt': start+timedelta(hours=1)}]
        with patch.object(self.store, '_fetch_html', return_value='fixture'), patch.object(self.store, '_french_tf1', return_value=rows):
            self.assertEqual(self.store._fetch_french_programs(provider), [])


if __name__ == '__main__':
    unittest.main()
