"""Home Assistant locale fallback and reminder language regressions."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

spec = importlib.util.spec_from_file_location("locale_app", Path(__file__).parents[1] / "app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class LocalizationTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        patcher = patch.object(app, "OPTIONS_FILE", Path(folder.name) / "options.json")
        patcher.start()
        self.addCleanup(patcher.stop)
        app.HA_LOCALE_CACHE.update(expires=0, value={})

    def test_invalid_or_missing_language_preserves_auto_default(self):
        self.assertEqual(app.load_options()["language"], "auto")
        app.save_options_file({"language": "es", "country": "nl"})
        self.assertEqual(app.load_options()["language"], "auto")
        with patch.object(app, "home_assistant_locale", return_value={}):
            self.assertEqual(app.effective_language(), "nl")

    def test_profile_override_and_installation_country_fallback(self):
        for country, expected in [("de", "de"), ("at", "de"), ("nl", "nl"), ("ch", "en"), ("be", "en"), ("no", "nb")]:
            app.save_options_file({"country": country, "language": "auto"})
            with patch.object(app, "home_assistant_locale", return_value={}):
                self.assertEqual(app.effective_language(), expected)
        with patch.object(app, "home_assistant_locale", return_value={"language": "fr-CH", "country": "CH"}):
            self.assertEqual(app.effective_language(), "fr")
            self.assertEqual(app.effective_language("it"), "it")
            self.assertEqual(app.effective_language("es"), "en")
        app.save_options_file({"country": "de", "language": "en"})
        with patch.object(app, "home_assistant_locale", side_effect=AssertionError("Explicit language must not query Core")):
            self.assertEqual(app.effective_language(), "en")

    def test_norwegian_profile_and_explicit_selection(self):
        for language in ("nb", "nb-NO", "no", "no-NO"):
            with self.subTest(language=language):
                with patch.object(app, "home_assistant_locale", return_value={"language": language}):
                    self.assertEqual(app.effective_language("auto"), "nb")
        app.save_options_file({"country": "de", "language": "nb"})
        self.assertEqual(app.load_options()["language"], "nb")
        self.assertEqual(app.effective_language(), "nb")
        self.assertEqual(app.translate("Speichern", "nb"), "Lagre")

    def test_config_is_cached_and_exposes_only_locale(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({"language": "nl", "country": "NL", "latitude": 52, "longitude": 4}).encode()
        with patch.dict(app.os.environ, {"SUPERVISOR_TOKEN": "test"}), patch.object(app, "urlopen", return_value=response) as request:
            self.assertEqual(app.home_assistant_locale(), {"language": "nl", "country": "NL"})
            self.assertEqual(app.home_assistant_locale(), {"language": "nl", "country": "NL"})
            request.assert_called_once()
            self.assertEqual(request.call_args.args[0].full_url, "http://supervisor/core/api/config")
            self.assertEqual(request.call_args.kwargs["timeout"], 3)

    def test_missing_or_unavailable_core_does_not_break_guide(self):
        with patch.dict(app.os.environ, {"SUPERVISOR_TOKEN": ""}), patch.object(app, "urlopen", side_effect=AssertionError("No token")):
            self.assertEqual(app.home_assistant_locale(), {})
        with patch.dict(app.os.environ, {"SUPERVISOR_TOKEN": "test"}), patch.object(app, "urlopen", side_effect=TimeoutError) as request:
            self.assertEqual(app.home_assistant_locale(), {})
            self.assertEqual(app.home_assistant_locale(), {})
            request.assert_called_once()

    def test_notification_language_preserves_original_programme(self):
        reminder = {"id": "example", "channel": "SRF 1", "title": "Ein Titel {minutes}", "start": "2030-01-01T20:15:00+01:00", "language": "fr"}
        response = MagicMock()
        with patch.dict(app.os.environ, {"SUPERVISOR_TOKEN": "test"}), patch.object(app, "urlopen", return_value=response) as request:
            app._ha_notification(reminder)
        body = json.loads(request.call_args.args[0].data)
        self.assertEqual(body["title"], app.translate("TV Guide – Erinnerung", "fr"))
        self.assertIn("Ein Titel {minutes}", body["message"])
        self.assertIn("20:15", body["message"])
        self.assertIn("SRF 1", body["message"])
        self.assertNotIn("beginnt", body["message"])

    def test_norwegian_reminder_preserves_programme_title_and_time(self):
        reminder = {"id": "norwegian", "channel": "NRK 1", "title": "Ein Titel {minutes}", "start": "2030-01-01T20:15:00+01:00", "language": "nb"}
        with patch.dict(app.os.environ, {"SUPERVISOR_TOKEN": "test"}), patch.object(app, "urlopen", return_value=MagicMock()) as request:
            app._ha_notification(reminder)
        body = json.loads(request.call_args.args[0].data)
        self.assertIn("Påminnelse", body["title"])
        self.assertIn("Ein Titel {minutes}", body["message"])
        self.assertIn("20:15", body["message"])
        self.assertIn("NRK 1", body["message"])
        self.assertNotIn("beginnt", body["message"])


if __name__ == "__main__":
    unittest.main()
