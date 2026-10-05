"""Guide links must also work inside Home Assistant's app information page."""
import re
import unittest
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).parents[2]


class DocumentationTests(unittest.TestCase):
    def test_language_links_do_not_resolve_to_a_home_assistant_app(self):
        for filename in ("README.md", "tv-guide/README.md", "tv-guide/DOCS.md"):
            text = (ROOT / filename).read_text(encoding="utf-8")
            links = re.findall(r"\]\(([^)]+/manuals/[^)]+)\)", text)
            self.assertEqual(len(links), 8, filename)
            for language in ("de", "en", "es", "nl", "fr", "it", "nb", "sv"):
                expected = f"https://criticallimit.github.io/TV-Guide/manuals/{language}.html"
                self.assertIn(expected, links)
                self.assertEqual(urljoin("https://homeassistant.local/config/apps/tv_guide/info", expected), expected)
                self.assertTrue((ROOT / "docs/manuals" / f"{language}.html").is_file())
