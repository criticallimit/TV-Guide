"""Verify the shipped library and logo selection without network access."""
import base64
import hashlib
import importlib.util
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("library_app", ROOT / "app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
app = app.backend


class LogoLibraryTests(unittest.TestCase):
    def test_country_match_across_all_identities_precedes_foreign_namesake(self):
        registry = {
            "aliases": {"": ["foreign"], "generic": ["foreign"], "specific": ["missing-theme", "local"]},
            "assets": {
                "foreign": {"countries": ["no"], "light": "foreign.svg", "dark": "foreign-dark.svg"},
                "missing-theme": {"countries": ["dk"], "dark": "dark.svg"},
                "local": {"countries": ["dk"], "light": "local.svg"},
            },
        }
        with patch.object(app, "EUROPE_LOGO_LIBRARY", registry):
            for field in ("source_name", "source_id", "xmltv_ids", "aliases"):
                channel = {"id": "dk_station", "name": "Generic", field: ["Specific.dk"] if field in {"xmltv_ids", "aliases"} else "Specific.dk"}
                with self.subTest(field=field):
                    self.assertEqual(app._europe_logo_source(channel, "light"), "local.svg")
                    self.assertEqual(app._europe_logo_source(channel, "dark"), "dark.svg")
            self.assertEqual(app._europe_logo_source({"name": "Generic", "source_country": "dk"}, "light"), "foreign.svg")
            self.assertEqual(app._europe_logo_source({"name": "Generic"}, "light"), "foreign.svg")
            self.assertEqual(app._europe_logo_source({"name": "Unknown"}, "light"), "")

    def test_entire_europe_pack_has_valid_assets_and_standalone_responses(self):
        registry = app.EUROPE_LOGO_LIBRARY
        self.assertTrue(registry["assets"])
        root = (app.WWW / "logos/europe").resolve()
        checked_assets = {}
        self.addCleanup(app._standalone_europe_logo.cache_clear)
        for asset_id, entry in registry["assets"].items():
            with self.subTest(asset=asset_id):
                asset = (app.WWW / entry["local_asset"]).resolve()
                self.assertIn((root / "assets").resolve(), asset.parents)
                if asset not in checked_assets:
                    checked_assets[asset] = asset.read_bytes()
                data = checked_assets[asset]
                self.assertTrue(data)
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry["source_sha256"])
                for theme in ("light", "dark"):
                    path = (app.WWW / entry[theme]).resolve()
                    self.assertIn((root / theme).resolve(), path.parents)
                    original = ET.fromstring(path.read_bytes())
                    self.assertEqual(original.attrib["viewBox"], "0 0 260 64")
                    images = original.findall("{http://www.w3.org/2000/svg}image")
                    self.assertEqual(len(images), 1)
                    self.assertEqual((path.parent / images[0].attrib["href"]).resolve(), asset)
                    rendered = ET.fromstring(app._standalone_europe_logo(path))
                    embedded = rendered.find("{http://www.w3.org/2000/svg}image").attrib["href"]
                    header, encoded = embedded.split(",", 1)
                    self.assertEqual(header, "data:" + app._logo_mime(str(asset), None, data) + ";base64")
                    self.assertEqual(base64.b64decode(encoded, validate=True), data)
                    for node in rendered.iter():
                        href = node.attrib.get("href", "")
                        self.assertTrue(not href or href.startswith(("data:image/", "#")), href)
        for key, asset_ids in registry["aliases"].items():
            self.assertTrue(asset_ids, key)
            for asset_id in asset_ids:
                self.assertIn(asset_id, registry["assets"], key)

    def test_every_catalog_channel_has_two_self_contained_assets(self):
        paths = set()
        for entry in app.LOGO_LIBRARY["channels"].values():
            self.assertIn(entry["country"], app.COUNTRIES)
            for theme in ("light", "dark"):
                paths.add(entry[theme])
        for name in paths:
            with self.subTest(path=name):
                path = (app.WWW / name).resolve()
                self.assertIn(app.WWW.resolve(), path.parents)
                svg = ET.fromstring(path.read_bytes())
                self.assertEqual(svg.attrib.get("viewBox"), "0 0 260 64")
                for element in svg.iter():
                    self.assertNotIn(element.tag.rsplit("}", 1)[-1], ("feMorphology", "feGaussianBlur"))
                    href = element.attrib.get("href", "")
                    self.assertTrue(not href or href.startswith(("data:image/", "#")), href)

    def test_all_main_channels_have_real_brand_assets(self):
        for country in app.COUNTRIES:
            catalog = app.CHANNELS if country == "de" else app.COUNTRY_CATALOGS[country]
            for original in catalog["channels"]:
                channel = {**original, "source_country": country}
                curated = app.LOGO_LIBRARY["channels"].get(channel["id"])
                if curated:
                    self.assertEqual(curated["country"], country)
                    self.assertEqual(curated["kind"], "brand", channel["name"])
                for theme in ("light", "dark"):
                    source = app._logo_source_for_channel(channel, theme)
                    self.assertTrue(source, f"{country}/{channel['name']}/{theme}")
                    self.assertFalse(source.startswith(("http://", "https://")), source)
                    path = app.normalized_logo_path(channel, theme)
                    self.assertTrue(path.is_file(), f"{country}/{channel['name']}/{theme}: {path}")

    def test_bundled_logos_override_old_feed_and_cache_fields(self):
        with patch.object(app, "_read_logo_source", side_effect=AssertionError("Must stay offline")):
            for country in app.COUNTRIES:
                catalog = app.CHANNELS if country == "de" else app.COUNTRY_CATALOGS[country]
                original = catalog["channels"][0]
                channel = {
                    **original,
                    "source_country": country,
                    "logo": "https://invalid.example/old.png",
                    "logo_url": "https://invalid.example/old.png",
                }
                for theme in ("light", "dark"):
                    source = app._logo_source_for_channel(channel, theme)
                    self.assertTrue(source, f"{country}/{channel['name']}/{theme}")
                    self.assertFalse(source.startswith(("http://", "https://")), source)
                    self.assertTrue(app.normalized_logo_path(channel, theme).is_file())

    def test_manifest_coverage_matches_the_library(self):
        manifest = json.loads((ROOT / "data/logo_manifest.json").read_text(encoding="utf-8"))
        for country, totals in manifest["countries"].items():
            entries = [c for c in app.LOGO_LIBRARY["channels"].values() if c["country"] == country]
            self.assertEqual(totals["channels"], len(entries))
            self.assertEqual(totals["main_channels"], sum(c["main"] for c in entries))
            self.assertEqual(totals["name_fallbacks"], sum(c["kind"] == "name" for c in entries))


if __name__ == "__main__":
    unittest.main()
