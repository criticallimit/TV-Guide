"""Swedish country, official SVT schedules and UI wiring."""
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sweden_app", ROOT / "app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
app = app.backend


class SwedenTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        root = Path(folder.name)
        paths = patch.multiple(
            app,
            OPTIONS_FILE=root / "options.json",
            CACHE_FILE=root / "feed.xml.gz",
            PARSED_CACHE_FILE=root / "parsed.json",
            CHANNEL_PREFS_FILE=root / "order.json",
        )
        paths.start()
        self.addCleanup(paths.stop)
        self.store = app.EPGStore("se")

    def test_country_and_catalog_are_consistent(self):
        countries = app.COUNTRIES
        self.assertEqual(countries["se"]["timezone"], "Europe/Stockholm")
        self.assertEqual(countries["se"]["sources"], ["https://www.open-epg.com/files/sweden1.xml.gz"])
        self.assertEqual(countries["se"]["catalog"], "channels_se.json")

        channels = app.COUNTRY_CATALOGS["se"]["channels"]
        self.assertEqual(len(channels), 16)
        self.assertEqual([channel["order"] for channel in channels], list(range(1, 17)))
        self.assertEqual(len({channel["id"] for channel in channels}), 16)

        ids = {xmltv_id for channel in channels for xmltv_id in channel["xmltv_ids"]}
        for required in {
            "SVT1.se", "SVT2.se", "TV4.se", "Kanal5.se", "Sjuan.se",
            "SVT24.se", "Kunskapskanalen.se", "TV10.se", "TV4Fakta.se",
        }:
            self.assertIn(required, ids)

    def test_sweden_and_swedish_are_enabled_in_addon_schema(self):
        config = (ROOT / "config.yaml").read_text(encoding="utf-8")
        self.assertIn('country: "list(' + "|".join(app.COUNTRIES) + ')"', config)
        self.assertIn('language: "list(auto|da|de|en|nl|fr|it|nb|sv)"', config)

    def test_svt_official_page_is_scoped_by_station_date_and_timezone(self):
        provider = app.COUNTRIES["se"]["providers"]["se_svt1"]

        def fetch(url, label):
            day = url.split("date=", 1)[1].split("&", 1)[0]
            return f"""
            <h3>Tablå för SVT 1</h3>
            <div>Klockan 20:00 - Kvällsprogram {day} 20:00</div>
            <div>Klockan 21:00 - Rapport 21:00</div>
            <div>Klockan 00:15 - Nattprogram 00:15</div>
            <h3>Tablå för SVT 2</h3>
            <div>Klockan 20:00 - Fel kanal 20:00</div>
            """

        with patch.object(self.store, "_fetch_html", side_effect=fetch):
            rows = self.store._fetch_official_programs("se_svt1", provider)

        titles = [row["title"] for row in rows]
        self.assertTrue(any(title.startswith("Kvällsprogram") for title in titles))
        self.assertIn("Rapport", titles)
        self.assertIn("Nattprogram", titles)
        self.assertNotIn("Fel kanal", titles)
        for row in rows:
            start = datetime.fromisoformat(row["start"])
            self.assertIsNotNone(start.utcoffset())
            self.assertEqual(
                start.utcoffset(),
                start.astimezone(ZoneInfo("Europe/Stockholm")).utcoffset(),
            )

    def test_five_svt_channels_have_verified_direct_providers(self):
        providers = app.COUNTRIES["se"]["providers"]
        self.assertEqual(
            {key for key, item in providers.items() if item["kind"] == "svt"},
            {"se_svt1", "se_svt2", "se_svtbarn", "se_kunskapskanalen", "se_svt24"},
        )
        self.assertEqual({key for key, item in providers.items() if item["kind"] == "tv4"},
                         {"se_tv4", "se_sjuan", "se_tv12", "se_tv4fakta"})


if __name__ == "__main__":
    unittest.main()
