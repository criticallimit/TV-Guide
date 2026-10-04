"""Mixed personal selections must preserve country stores, legacy data and filter independence."""
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

spec = importlib.util.spec_from_file_location("personal_app", Path(__file__).parents[1] / "app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
app = app.backend


class PersonalChannelTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        root = Path(folder.name)
        paths = patch.multiple(app, OPTIONS_FILE=root / "options.json", CHANNEL_PREFS_FILE=root / "order.json",
                               CACHE_FILE=root / "epg.gz", PARSED_CACHE_FILE=root / "epg.json")
        paths.start()
        self.addCleanup(paths.stop)
        self.stores = {code: app.EPGStore(code) for code in ["ch", "de", "at"]}
        self.store = self.stores["ch"]
        registry = patch.multiple(app, STORE=self.store, COUNTRY_STORES=self.stores)
        registry.start()
        self.addCleanup(registry.stop)
        freshness = patch.object(app.EPGStore, "ensure_fresh_async")
        self.freshness = freshness.start()
        self.addCleanup(freshness.stop)
        self.personal = app.PersonalChannels(app)
        personal = patch.object(app, "PERSONAL_CHANNELS", self.personal)
        personal.start()
        self.addCleanup(personal.stop)
        self.keys = [f"{code}:{self.stores[code].channels[0]['id']}" for code in ["ch", "de", "at"]]
        now = datetime.now(app.EPG_TIMEZONE)
        for code, store in self.stores.items():
            store.channels[0].update(available=True, programs=[{
                "title": code + " programme", "start": (now - timedelta(minutes=10)).isoformat(),
                "end": (now + timedelta(hours=1)).isoformat(), "_source": code + " official",
            }])

    def test_catalogue_contains_every_country_without_network_refresh(self):
        settings = self.personal.settings(self.store)
        self.assertEqual({item["source_country"] for item in settings["channels"]}, set(app.COUNTRIES))
        self.assertEqual(len({item["id"] for item in settings["channels"]}), len(settings["channels"]))
        self.freshness.assert_not_called()
        self.assertEqual(set(self.stores), {"ch", "de", "at"})

    def test_foreign_catalogue_logo_does_not_start_a_country_store_or_refresh(self):
        item = app.COUNTRY_CATALOGS["no"]["channels"][0]
        channel = self.personal.logo_channel("no:" + item["id"])
        self.assertEqual(channel["source_channel_id"], item["id"])
        self.assertNotIn("no", self.stores)
        self.freshness.assert_not_called()

    def test_existing_order_and_hidden_channels_are_migrated_without_rewriting(self):
        ids = list(reversed(app.base_channel_ids(self.store)))
        app.save_channel_preferences(ids, [ids[0]], self.store)
        path = app.channel_preferences_file(self.store)
        before = path.read_bytes()
        legacy = self.personal.load(self.store)
        self.assertEqual(legacy["order"], [f"ch:{item}" for item in ids[1:]])
        self.personal.save(legacy["order"], ["ch"], self.store)
        self.assertEqual(path.read_bytes(), before)

    def test_filters_never_remove_selection_and_round_trip_survives_country_change(self):
        self.personal.save(self.keys, ["ch", "de", "at"], self.store)
        self.personal.save(self.keys, [], self.store)
        restarted = app.PersonalChannels(app)
        self.assertEqual(restarted.load(self.stores["at"]), {"order": self.keys, "countries": []})
        self.assertEqual(restarted.guide(self.stores["de"])["custom_channel_ids"], self.keys)

    def test_mixed_payload_keeps_programmes_sources_and_main_ids_separate(self):
        self.personal.save(list(reversed(self.keys)), ["ch"], self.store)
        payload = self.personal.guide(self.store)
        self.assertEqual(payload["main_channel_ids"], app.base_channel_ids(self.store))
        self.assertEqual(payload["custom_channel_ids"], list(reversed(self.keys)))
        channels = {item["id"]: item for item in payload["channels"]}
        for key in self.keys:
            country, raw_id = key.split(":", 1)
            item = channels[key]
            self.assertEqual(item["source_channel_id"], raw_id)
            self.assertEqual(item["programs"][0]["title"], country + " programme")
            self.assertEqual(item["programs"][0]["source"], country + " official")
            self.assertIn(key.replace(":", "%3A"), item["logo_normalized_dark"])

    def test_only_selected_country_sources_are_refreshed_and_limit_is_global(self):
        app.save_options_file({"max_channels": 2})
        self.personal.save(self.keys, [], self.store)
        payload = self.personal.guide(self.store)
        self.assertEqual(payload["custom_channel_ids"], self.keys[:2])
        self.assertEqual(self.freshness.call_count, 2)  # active main reused + selected German store
        self.personal.save([], [], self.store)
        self.freshness.reset_mock()
        self.assertEqual(self.personal.guide(self.store)["custom_channel_ids"], [])
        self.assertEqual(self.freshness.call_count, 1)

    def test_offline_source_does_not_erase_other_countries_or_selection(self):
        self.stores["at"].channels[0].update(available=False, programs=[])
        self.personal.save(self.keys, [], self.store)
        payload = self.personal.guide(self.store)
        channels = {item["id"]: item for item in payload["channels"]}
        self.assertEqual(channels[self.keys[2]]["data_state"], "source_unavailable")
        self.assertTrue(channels[self.keys[0]]["programs"])
        self.assertTrue(channels[self.keys[1]]["programs"])
        self.assertEqual(self.personal.load(self.store)["order"], self.keys)

    def test_unknown_ids_and_countries_cannot_replace_valid_selection(self):
        self.personal.save(self.keys, ["ch"], self.store)
        for order, countries in [(["de:missing"], ["de"]), (["xx:ard"], []), (self.keys, ["xx"]), ([None], [])]:
            with self.subTest(order=order, countries=countries), self.assertRaises(ValueError):
                self.personal.save(order, countries, self.store)
        self.assertEqual(self.personal.load(self.store)["order"], self.keys)

    def test_cached_extra_channel_remains_selectable_after_registry_restart(self):
        store = self.stores["at"]
        store.channels.append({"id": "epg_extra", "name": "Regional extra", "available": False, "programs": []})
        store._save_parsed_cache("fixture")
        self.personal.save(["at:epg_extra"], ["at"], self.store)
        del self.stores["at"]
        self.assertIn("at:epg_extra", self.personal.catalogue(self.store))
        self.assertEqual(self.personal.guide(self.store)["custom_channel_ids"], ["at:epg_extra"])

    def test_personal_reset_keeps_original_country_preferences(self):
        ids = list(reversed(app.base_channel_ids(self.store)))
        app.save_channel_preferences(ids, [], self.store)
        self.personal.save(self.keys, [], self.store)
        self.personal.reset(self.store)
        self.assertEqual(app.load_channel_preferences(self.store)["order"], ids)
        self.assertEqual(self.personal.load(self.store)["order"], [f"ch:{item}" for item in app.base_channel_ids(self.store)])

    def test_real_api_saves_global_selection_and_serves_foreign_bundled_logo(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f"http://127.0.0.1:{server.server_port}"
        def post(value):
            request = Request(base + "/api/personal-channels", data=json.dumps(value).encode(),
                              headers={"Content-Type": "application/json"})
            with urlopen(request) as response:
                return json.load(response)
        self.assertTrue(post({"order": self.keys, "countries": []})["ok"])
        with patch.object(app, "STORE", self.stores["at"]):
            with urlopen(base + "/api/personal-channels") as response:
                self.assertEqual(json.load(response)["order"], self.keys)
            with urlopen(base + "/api/guide") as response:
                self.assertEqual(json.load(response)["custom_channel_ids"], self.keys)
        with urlopen(base + "/api/channel-logo/" + self.keys[1].replace(":", "%3A") + "/dark.svg") as response:
            self.assertIn(b"<svg", response.read())
        with self.assertRaises(HTTPError) as invalid:
            post({"order": ["at:missing"], "countries": []})
        self.assertEqual(invalid.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
