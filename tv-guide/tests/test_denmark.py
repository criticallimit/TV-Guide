"""Danish country catalogue and add-on wiring."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("denmark_app", ROOT / "app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
app = app.backend


class DenmarkTests(unittest.TestCase):
    def test_country_and_catalog_are_consistent(self):
        countries = app.COUNTRIES
        self.assertEqual(countries["dk"]["timezone"], "Europe/Copenhagen")
        self.assertEqual(countries["dk"]["sources"], ["https://www.open-epg.com/files/denmark.xml.gz"])
        self.assertEqual(countries["dk"]["catalog"], "channels_dk.json")

        channels = app.COUNTRY_CATALOGS["dk"]["channels"]
        self.assertEqual(len(channels), 18)
        self.assertEqual([channel["order"] for channel in channels], list(range(1, 19)))
        self.assertEqual(len({channel["id"] for channel in channels}), 18)

        ids = {xmltv_id for channel in channels for xmltv_id in channel["xmltv_ids"]}
        for required in {
            "DR1.dk", "DR2.dk", "DRRamasjang.dk", "TV2.dk", "TV3.dk",
            "TV2Charlie.dk", "TV2News.dk", "Kanal5.dk", "Kanal4.dk", "dk4.dk",
        }:
            self.assertIn(required, ids)

    def test_denmark_is_enabled_in_addon_schema(self):
        config = (ROOT / "config.yaml").read_text(encoding="utf-8")
        self.assertIn('country: "list(de|at|ch|nl|be|dk|no|fr|se|gb)"', config)

    def test_denmark_has_direct_dr_and_shared_tv2_schedules_with_xmltv_fallback(self):
        country = app.COUNTRIES["dk"]
        self.assertEqual(set(country["providers"]), {channel["id"] for channel in app.COUNTRY_CATALOGS["dk"]["channels"]})
        for channel, marker in {"dk_dr1": "20875", "dk_dr2": "20876", "dk_drramasjang": "20892"}.items():
            self.assertEqual(country["providers"][channel]["kind"], "dr")
            self.assertEqual(country["providers"][channel]["marker"], marker)
            self.assertEqual(country["secondary_providers"][channel]["kind"], "tv2dk")
        self.assertTrue(all(provider["kind"] == "tv2dk" for channel, provider in country["providers"].items()
                            if channel not in country["secondary_providers"]))


if __name__ == "__main__":
    unittest.main()
