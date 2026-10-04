"""Country switching must never mix schedules, preferences or regional feeds."""
import importlib.util
import json
import tempfile
import threading
import unittest
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

spec = importlib.util.spec_from_file_location("country_app", Path(__file__).parents[1] / "app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class CountryTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        root = Path(self.folder.name)
        self.paths = patch.multiple(app, OPTIONS_FILE=root / "options.json", CACHE_FILE=root / "feed.xml.gz",
                                    PARSED_CACHE_FILE=root / "parsed.json", CHANNEL_PREFS_FILE=root / "order.json")
        self.paths.start()
        self.addCleanup(self.paths.stop)

    def store(self, country):
        return app.EPGStore(country)

    def test_default_preserves_german_installation_and_invalid_country_is_safe(self):
        self.assertEqual(app.load_options()["country"], "de")
        store = self.store("de")
        self.assertIs(store.catalog, app.CHANNELS)
        self.assertEqual(store.cache_file, app.CACHE_FILE)
        self.assertEqual(store.parsed_cache_file, app.PARSED_CACHE_FILE)
        app.save_options_file({"country": "../../elsewhere"})
        self.assertEqual(app.EPGStore().country, "de")
        app.save_options_file({"country": "be"})
        self.assertEqual(app.EPGStore().country, "be")

    def test_country_catalogues_and_sources_are_isolated(self):
        for country in ["at", "ch", "nl", "be"]:
            store = self.store(country)
            ids = app.base_channel_ids(store)
            self.assertEqual(len(ids), len(set(ids)))
            self.assertTrue(all(key.startswith(country + "_") for key in ids))
            self.assertTrue(all(source.endswith("." + country) for ch in store.catalog["channels"] for source in ch["xmltv_ids"]))
            for channel in store.catalog["channels"]:
                for field in ["logo_file", "logo_file_light"]:
                    if channel.get(field):
                        self.assertTrue((app.WWW / channel[field]).is_file(), channel[field])
            self.assertNotIn(app.OPEN_EPG_URL, store._candidate_urls())
            self.assertNotEqual(store.cache_file, app.CACHE_FILE)
        self.assertEqual(self.store("de")._candidate_urls(), app.BUILTIN_EPG_URLS)

    def test_preferences_survive_round_trip_without_cross_country_ids(self):
        de, at = self.store("de"), self.store("at")
        german = list(reversed(app.base_channel_ids(de)))
        austrian = list(reversed(app.base_channel_ids(at)))
        app.save_channel_preferences(german, [german[0]], de)
        app.save_channel_preferences(austrian + german, [austrian[0]], at)
        self.assertEqual(app.load_channel_preferences(de), {"order": german, "hidden": [german[0]]})
        self.assertEqual(app.load_channel_preferences(at), {"order": austrian, "hidden": [austrian[0]]})
        app.reset_channel_preferences(at)
        self.assertEqual(app.load_channel_preferences(de)["order"], german)
        self.assertEqual(app.load_channel_preferences(at)["order"], app.base_channel_ids(at))

    def test_background_cache_writes_remain_bound_to_original_country(self):
        de, at = self.store("de"), self.store("at")
        now = datetime.now(app.EPG_TIMEZONE)
        for store in [de, at]:
            store.channels[0]["programs"] = [{"title": store.country, "start": now.isoformat(), "end": (now + timedelta(hours=1)).isoformat()}]
            store.channels[0]["available"] = True
            with patch.object(app, "STORE", at):
                store._save_parsed_cache("test")
        self.assertEqual(self.store("de").channels[0]["programs"][0]["title"], "de")
        self.assertEqual(self.store("at").channels[0]["programs"][0]["title"], "at")
        wrong = json.loads(de.parsed_cache_file.read_text())
        at.parsed_cache_file.write_text(json.dumps(wrong))
        self.assertFalse(any(ch["programs"] for ch in self.store("at").channels))

    def test_same_feed_id_in_two_countries_does_not_share_dynamic_channel_id(self):
        source = Path(self.folder.name) / "source.xml"
        source.write_text('<tv><channel id="regional"><display-name>Regional</display-name></channel></tv>')
        ids = []
        for country in ["de", "at", "be"]:
            store = self.store(country)
            with patch.object(store, "_open_xml", side_effect=lambda: source.open("rb")):
                ids.append(next(iter(store._build_channel_map())))
        self.assertEqual(len(set(ids)), 3)

    def test_swiss_official_parser_checks_station_date_and_timezone(self):
        store = self.store("ch")
        today = datetime.now(app.EPG_TIMEZONE).date()
        day = today.isoformat()
        stale = (today - timedelta(days=5)).isoformat()
        def slot(title, date=day, suffix="+02:00"):
            return {"title": title, "startTime": date + "T12:00:00" + suffix, "endTime": date + "T13:00:00" + suffix}
        data = {"programGuide": [
            {"channel": {"title": "SRF 1"}, "programList": [slot("Valid"), slot("Stale", stale), slot("No timezone", suffix="")]},
            {"channel": {"title": "SRF zwei"}, "programList": [slot("Wrong station")]},
        ]}
        with patch.object(store, "_fetch_html", return_value=json.dumps(data)):
            result = store._fetch_country_official_programs(app.COUNTRIES["ch"]["providers"]["ch_srf1"])
        self.assertEqual([p["title"] for p in result], ["Valid"])
        self.assertIn(day, result[0]["_source_url"])

    def test_play_rejects_page_for_other_country_channel_or_date(self):
        store = self.store("be")
        provider = app.COUNTRIES["be"]["providers"]["be_play"]
        page = '<script>self.__next_f.push([1,"{\\"activeBrand\\":\\"crime\\",\\"activeDate\\":\\"2026-10-04\\"}"])</script>'
        with patch.object(store, "_fetch_html", return_value=page):
            self.assertEqual(store._fetch_country_official_programs(provider), [])

    def test_orf_reads_dated_broadcast_and_ignores_metadata_and_other_stations(self):
        store = self.store("at")
        day = datetime.now(app.EPG_TIMEZONE).date().isoformat()
        page = f'''<li data-channel="orf1" data-start-time="{day}T12:00:00+02:00" data-end-time="{day}T13:00:00+02:00">
        <div class="series-title"><a>Actual &amp; programme</a></div><div class="episode-title">Episode</div><svg><title>UT 301</title></svg></li>
        <li data-channel="orf2" data-start-time="{day}T12:00:00+02:00" data-end-time="{day}T13:00:00+02:00"><div class="series-title">Wrong channel</div></li>'''
        with patch.object(store, "_fetch_html", return_value=page):
            programmes = store._fetch_country_official_programs(app.COUNTRIES["at"]["providers"]["at_orf1"])
        self.assertEqual([p["title"] for p in programmes], ["Actual & programme"])
        self.assertEqual(programmes[0]["subtitle"], "Episode")

    def test_play_reads_split_embedded_data_and_preserves_exact_duration(self):
        store = self.store("be")
        now = datetime.now(app.EPG_TIMEZONE).replace(hour=6, minute=0, second=0, microsecond=0)
        item = {"dateString": now.date().isoformat(), "timestamp": int(now.timestamp()), "duration": 28800,
                "programTitle": "Live programme", "episodeTitle": "Part one"}
        data = json.dumps({"activeBrand": "play", "activeDate": now.date().isoformat(), "program": item}, separators=(",", ":"))
        midpoint = len(data) // 2
        page = "".join('<script>self.__next_f.push(' + json.dumps([1, chunk]) + ')</script>' for chunk in [data[:midpoint], data[midpoint:]])
        with patch.object(store, "_fetch_html", return_value=page):
            programmes = store._fetch_country_official_programs(app.COUNTRIES["be"]["providers"]["be_play"])
        self.assertEqual([p["title"] for p in programmes], ["Live programme"])
        self.assertEqual(datetime.fromisoformat(programmes[0]["end"]) - datetime.fromisoformat(programmes[0]["start"]), timedelta(hours=8))

    def test_settings_api_switches_atomically_and_reuses_country_store(self):
        de = self.store("de")
        registry = {"de": de}
        with patch.object(app, "STORE", de), patch.object(app, "COUNTRY_STORES", registry), \
                patch.object(app, "update_addon_options"), patch.object(app.EPGStore, "refresh"):
            server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
            base = f"http://127.0.0.1:{server.server_port}"
            def post(path, payload):
                req = Request(base + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
                with urlopen(req) as response:
                    return json.load(response)
            wanted = {"country": "at", "language": "fr", "default_view": "now", "columns_desktop": 5, "max_channels": 0,
                      "theme_mode": "auto", "refresh_minutes": 180, "notification_service": "persistent_notification.create"}
            self.assertTrue(post("/api/settings", wanted)["country_changed"])
            with urlopen(base + "/api/settings") as response:
                self.assertEqual(json.load(response)["language"], "fr")
            with self.assertRaises(HTTPError) as unsupported:
                post("/api/settings", {**wanted, "language": "es"})
            self.assertEqual(unsupported.exception.code, 400)
            legacy = {key: value for key, value in wanted.items() if key != "language"}
            post("/api/settings", legacy)
            self.assertEqual(app.load_options()["language"], "fr")
            austrian = app.STORE
            self.assertEqual(austrian.country, "at")
            with urlopen(base + "/api/channels") as response:
                self.assertTrue(json.load(response)["channels"][0]["id"].startswith("at_"))
            with self.assertRaises(HTTPError) as stale:
                post("/api/channel-settings", {"country": "de", "order": ["ard"], "hidden": []})
            self.assertEqual(stale.exception.code, 409)
            post("/api/settings", {**wanted, "country": "de"})
            self.assertIs(app.STORE, de)
            post("/api/settings", wanted)
            self.assertIs(app.STORE, austrian)
            with self.assertRaises(HTTPError) as invalid:
                post("/api/settings", {**wanted, "country": "xx"})
            self.assertEqual(invalid.exception.code, 400)
            self.assertEqual(app.STORE.country, "at")


if __name__ == "__main__":
    unittest.main()
