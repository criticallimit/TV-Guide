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
    def test_image_urls_change_with_artwork_assignment_and_text_fallback_name(self):
        channel = {"id": "test_station", "name": "Test station"}
        with patch.object(app, "_logo_source_for_channel", return_value="old.svg"):
            before = app.normalized_logo_urls(channel)
            self.assertEqual(before, app.normalized_logo_urls(channel))
        with patch.object(app, "_logo_source_for_channel", return_value="new.svg"):
            after = app.normalized_logo_urls(channel)
        for old, new in zip(before, after):
            self.assertNotEqual(old, new)
            self.assertEqual(old.split("?", 1)[0], new.split("?", 1)[0])
        with patch.object(app, "_logo_source_for_channel", return_value=""):
            self.assertNotEqual(app.normalized_logo_urls(channel),
                                app.normalized_logo_urls({**channel, "name": "New station name"}))

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
                    self.assertFalse(source.startswith("logos/uk/"), f"Text fallback for main channel: {channel['name']}")
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

    def test_reviewed_updates_resolve_offline_and_preserve_embedded_artwork_hashes(self):
        updates = json.loads((ROOT / "data/logo_updates.json").read_text(encoding="utf-8"))
        updates["channels"] = {}
        for name in updates["source_parts"]:
            part = json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))
            self.assertFalse(updates["channels"].keys() & part["channels"].keys(), name)
            updates["channels"].update(part["channels"])
        library_ids = set()
        for name in updates["library_parts"]:
            part = json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))
            self.assertFalse(library_ids & part["channels"].keys(), name)
            library_ids.update(part["channels"])
        self.assertEqual(library_ids, set(updates["channels"]))
        countries = json.loads((ROOT / "data/countries.json").read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / "data/logo_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(set(manifest["countries"]), set(countries))
        excluded = {entry["url"] for entry in updates["excluded_feed_images"]}
        checked = set()
        for channel_id, entry in app.LOGO_LIBRARY["channels"].items():
            if entry.get("reviewed_update") or entry["asset"].startswith("acquired-"):
                self.assertIn(channel_id, updates["channels"], f"Withdrawn artwork still registered: {channel_id}")
        for channel_id, update in updates["channels"].items():
            entry = app.LOGO_LIBRARY["channels"][channel_id]
            self.assertEqual(entry["kind"], "brand", channel_id)
            for key in ("country", "name", "source_ids", "main"):
                self.assertEqual(entry[key], update[key], channel_id)
            self.assertNotIn(update.get("source_url"), excluded)
            if "source_url" in update:
                self.assertRegex(update["source_sha256"], r"^[0-9a-f]{64}$")
            for theme in ("light", "dark"):
                with patch.object(app, "_read_logo_source", side_effect=AssertionError("Must stay offline")):
                    channel = {"id": channel_id, "name": update["name"], "source_country": update["country"]}
                    self.assertEqual(app._logo_source_for_channel(channel, theme), entry[theme])
                    personal = {**channel, "id": "personal_" + channel_id, "source_channel_id": channel_id}
                    self.assertEqual(app._logo_source_for_channel(personal, theme), entry[theme])
                if entry[theme] in checked or not entry["asset"].startswith("acquired-"):
                    continue
                checked.add(entry[theme])
                svg = ET.parse(app.WWW / entry[theme]).getroot()
                images = svg.findall("{http://www.w3.org/2000/svg}image")
                self.assertEqual(len(images), 1)
                encoded = images[0].attrib["href"].split(",", 1)[1]
                raw = base64.b64decode(encoded, validate=True)
                metadata = app.LOGO_LIBRARY["assets"][entry["asset"]]
                self.assertEqual(hashlib.sha256(raw).hexdigest(), metadata["normalized_sha256"])


if __name__ == "__main__":
    unittest.main()
