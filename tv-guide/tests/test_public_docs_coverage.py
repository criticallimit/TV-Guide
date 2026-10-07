"""Keep country, language, GitHub Pages and manual coverage in sync."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
DOCS = REPO / "docs"

COUNTRIES = ["de", "at", "ch", "nl", "be", "dk", "no", "fr", "se", "gb"]
COUNTRY_KEYS = [
    "Deutschland", "Österreich", "Schweiz", "Niederlande", "Belgien",
    "Dänemark", "Norwegen", "Frankreich", "Schweden", "Großbritannien",
]
UI_LANGUAGES = ["da", "de", "en", "nl", "fr", "it", "nb", "sv"]
SITE_LANGUAGES = ["da", "de", "en", "es", "fr", "it", "nl", "nb", "sv"]

COUNTRY_NAMES = {
    "da": ["Belgien", "Danmark", "Frankrig", "Nederlandene", "Norge", "Schweiz", "Sverige", "Tyskland", "Østrig", "Storbritannien"],
    "de": ["Belgien", "Dänemark", "Deutschland", "Frankreich", "Niederlande", "Norwegen", "Österreich", "Schweden", "Schweiz", "Großbritannien"],
    "en": ["Austria", "Belgium", "Denmark", "France", "Germany", "Netherlands", "Norway", "Sweden", "Switzerland", "United Kingdom"],
    "es": ["Alemania", "Austria", "Bélgica", "Dinamarca", "Francia", "Noruega", "Países Bajos", "Suecia", "Suiza", "Reino Unido"],
    "fr": ["Allemagne", "Autriche", "Belgique", "Danemark", "France", "Norvège", "Pays-Bas", "Suède", "Suisse", "Royaume-Uni"],
    "it": ["Austria", "Belgio", "Danimarca", "Francia", "Germania", "Norvegia", "Paesi Bassi", "Svezia", "Svizzera", "Regno Unito"],
    "nl": ["België", "Denemarken", "Duitsland", "Frankrijk", "Nederland", "Noorwegen", "Oostenrijk", "Zweden", "Zwitserland", "Verenigd Koninkrijk"],
    "nb": ["Belgia", "Danmark", "Frankrike", "Nederland", "Norge", "Sveits", "Sverige", "Tyskland", "Østerrike", "Storbritannia"],
    "sv": ["Belgien", "Danmark", "Frankrike", "Nederländerna", "Norge", "Schweiz", "Sverige", "Tyskland", "Österrike", "Storbritannien"],
}


class PublicCoverageTests(unittest.TestCase):
    def test_addon_schema_has_all_supported_countries_and_ui_languages(self):
        config = (ROOT / "config.yaml").read_text(encoding="utf-8")
        self.assertIn('country: "list(' + "|".join(COUNTRIES) + ')"', config)
        self.assertIn('language: "list(auto|' + "|".join(UI_LANGUAGES) + ')"', config)

    def test_country_selector_and_locales_cover_every_country(self):
        index = (ROOT / "www" / "index.html").read_text(encoding="utf-8")
        for country in COUNTRIES:
            self.assertIn(f'value="{country}"', index)
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
            for country_name in COUNTRY_NAMES[language]:
                self.assertIn(country_name, page, f"{language} country {country_name}")

    def test_every_manual_exists_and_links_to_every_manual_language(self):
        for language in SITE_LANGUAGES:
            path = DOCS / "manuals" / f"{language}.html"
            self.assertTrue(path.is_file(), language)
            manual = path.read_text(encoding="utf-8")
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
            for country_name in COUNTRY_NAMES[language]:
                self.assertIn(country_name, manual, f"{language} markdown country {country_name}")

    def test_home_assistant_translations_cover_every_country(self):
        for language in UI_LANGUAGES:
            path = ROOT / "translations" / f"{language}.yaml"
            self.assertTrue(path.is_file(), language)
            translation = path.read_text(encoding="utf-8")
            for country_name in COUNTRY_NAMES[language]:
                self.assertIn(country_name, translation, f"{language} HA country {country_name}")

    def test_sitemap_contains_every_page_and_manual(self):
        sitemap = (DOCS / "sitemap.xml").read_text(encoding="utf-8")
        for language in SITE_LANGUAGES:
            page = "" if language == "de" else f"{language}.html"
            self.assertIn(f"https://criticallimit.github.io/TV-Guide/{page}", sitemap)
            self.assertIn(f"https://criticallimit.github.io/TV-Guide/manuals/{language}.html", sitemap)


if __name__ == "__main__":
    unittest.main()
