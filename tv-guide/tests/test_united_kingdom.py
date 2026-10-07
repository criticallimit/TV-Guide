"""United Kingdom catalogue, source redundancy and region policy."""
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("uk_app", Path(__file__).parents[1] / "app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
app = app.backend

class UnitedKingdomTests(unittest.TestCase):
    def test_country_registration_and_independent_sources(self):
        config = app.COUNTRIES["gb"]
        self.assertEqual(config["timezone"], "Europe/London")
        self.assertEqual(config["catalog"], "channels_gb.json")
        self.assertEqual(config["sources"], [
            "https://www.open-epg.com/files/unitedkingdom.xml.gz",
            "https://epgshare01.online/epgshare01/epg_ripper_UK1.xml.gz",
        ])

    def test_main_channels_and_london_reference_variants(self):
        catalog = app.COUNTRY_CATALOGS["gb"]["channels"]
        expected = [
            "BBC One", "BBC Two", "ITV1", "Channel 4", "Channel 5",
            "ITV2", "BBC Three", "BBC Four", "ITV3", "E4",
            "Film4", "More4", "ITV4", "U&Dave", "U&Drama",
            "U&Yesterday", "5USA", "Sky Mix", "BBC News", "Sky News",
        ]
        self.assertEqual([item["name"] for item in catalog], expected)
        self.assertEqual([item["order"] for item in catalog], list(range(1, 21)))
        self.assertTrue(all(item["id"].startswith("gb_") for item in catalog))
        self.assertTrue(all(source.endswith(".uk") for item in catalog for source in item["xmltv_ids"]))
        by_id = {item["id"]: item for item in catalog}
        self.assertIn("BBCOneLondon.uk", by_id["gb_bbcone"]["xmltv_ids"])
        self.assertIn("ITV1London.uk", by_id["gb_itv1"]["xmltv_ids"])
        self.assertTrue(all(item.get("xmltv_id_only") for item in catalog))

    def test_curated_channels_have_offline_logos(self):
        for original in app.COUNTRY_CATALOGS["gb"]["channels"]:
            channel = {**original, "source_country": "gb"}
            for theme in ("light", "dark"):
                source = app._logo_source_for_channel(channel, theme)
                self.assertTrue(source, f"{original['name']} / {theme}")
                self.assertFalse(source.startswith(("http://", "https://")))
                self.assertTrue(app.normalized_logo_path(channel, theme).is_file())


if __name__ == "__main__":
    unittest.main()
