"""Keep country, language, GitHub Pages and manual coverage in sync."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
DOCS = REPO / "docs"

COUNTRIES = json.loads((ROOT / "data" / "countries.json").read_text(encoding="utf-8"))
COUNTRY_KEYS = [country["name"] for country in COUNTRIES.values()]
UI_LANGUAGES = sorted(path.stem for path in (ROOT / "www" / "locales").glob("*.json"))
SITE_LANGUAGES = sorted(path.stem for path in (DOCS / "manuals").glob("*.html"))

# Spanish is a documentation language, not an add-on UI locale.
SPANISH_COUNTRIES = {
    "de": "Alemania", "at": "Austria", "ch": "Suiza", "nl": "Países Bajos",
    "be": "Bélgica", "dk": "Dinamarca", "no": "Noruega", "fr": "Francia",
    "se": "Suecia", "gb": "Reino Unido",
}


def country_names(language):
    if language == "es":
        return [SPANISH_COUNTRIES[code] for code in COUNTRIES]
    locale = json.loads((ROOT / "www" / "locales" / f"{language}.json").read_text(encoding="utf-8"))
    return [locale[key] for key in COUNTRY_KEYS]


class PublicCoverageTests(unittest.TestCase):
    def test_addon_schema_has_all_supported_countries_and_ui_languages(self):
        config = (ROOT / "config.yaml").read_text(encoding="utf-8")
        self.assertIn('country: "list(' + "|".join(COUNTRIES) + ')"', config)
        languages = re.search(r'language: "list\(([^)]+)\)"', config).group(1).split("|")
        self.assertCountEqual(languages, ["auto", *UI_LANGUAGES])

    def test_country_selector_and_locales_cover_every_country(self):
        index = (ROOT / "www" / "index.html").read_text(encoding="utf-8")
        selector = re.search(r'<select[^>]*id="settingCountry"[^>]*>(.*?)</select>', index, re.S)
        self.assertIsNotNone(selector)
        self.assertCountEqual(re.findall(r'value="([a-z]{2})"', selector.group(1)), COUNTRIES)
        for language in UI_LANGUAGES:
            locale = json.loads((ROOT / "www" / "locales" / f"{language}.json").read_text(encoding="utf-8"))
            for country_key in COUNTRY_KEYS:
                self.assertIn(country_key, locale)

    def test_every_public_language_page_has_full_language_and_manual_navigation(self):
        for language in SITE_LANGUAGES:
            path = DOCS / ("index.html" if language == "de" else f"{language}.html")
            self.assertTrue(path.is_file(), language)
            page = path.read_text(encoding="utf-8")
            for target in SITE_LANGUAGES:
                href = "./" if target == "de" else f"{target}.html"
                self.assertIn(f'href="{href}" lang="{target}"', page, f"{language}->{target}")
                self.assertIn(f'hreflang="{target}"', page, f"{language} hreflang {target}")
            for target in SITE_LANGUAGES:
                self.assertIn(f'manuals/{target}.html', page, f"{language} manual {target}")
            for country_name in country_names(language):
                self.assertIn(country_name, page, f"{language} country {country_name}")
            self.assertIn('href="en.html" lang="en"', page, f"{language} English link")
            expected_gb_flags = 2 if language == "en" else 1
            self.assertEqual(
                page.count('<img src="flags/gb.svg" alt="">'),
                expected_gb_flags,
                f"{language} English flag",
            )
            self.assertNotIn('textflag">EN', page, f"{language} legacy EN badge")

    def test_every_manual_exists_and_links_to_every_manual_language(self):
        for language in SITE_LANGUAGES:
            path = DOCS / "manuals" / f"{language}.html"
            self.assertTrue(path.is_file(), language)
            manual = path.read_text(encoding="utf-8")
            for country_name in country_names(language):
                self.assertIn(country_name, manual, f"{language} manual country {country_name}")
            for target in SITE_LANGUAGES:
                self.assertIn(f'href="{target}.html"', manual, f"{language}->{target}")

    def test_every_markdown_manual_links_every_manual_language(self):
        for language in SITE_LANGUAGES:
            path = DOCS / "manuals" / f"{language}.md"
            self.assertTrue(path.is_file(), language)
            manual = path.read_text(encoding="utf-8")
            for target in SITE_LANGUAGES:
                expected = f"/manuals/{target}.html"
                self.assertIn(expected, manual, f"{language} markdown->{target}")
            for country_name in country_names(language):
                self.assertIn(country_name, manual, f"{language} markdown country {country_name}")

    def test_home_assistant_translations_cover_every_country(self):
        for language in UI_LANGUAGES:
            path = ROOT / "translations" / f"{language}.yaml"
            self.assertTrue(path.is_file(), language)
            translation = path.read_text(encoding="utf-8")
            for country_name in country_names(language):
                self.assertIn(country_name, translation, f"{language} HA country {country_name}")

    def test_sitemap_contains_every_page_and_manual(self):
        sitemap = (DOCS / "sitemap.xml").read_text(encoding="utf-8")
        for language in SITE_LANGUAGES:
            page = "" if language == "de" else f"{language}.html"
            self.assertIn(f"https://criticallimit.github.io/TV-Guide/{page}", sitemap)
            self.assertIn(f"https://criticallimit.github.io/TV-Guide/manuals/{language}.html", sitemap)


if __name__ == "__main__":
    unittest.main()
