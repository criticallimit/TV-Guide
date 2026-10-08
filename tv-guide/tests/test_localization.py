"""Home Assistant locale fallback and reminder language regressions."""
import importlib.util
import json
import tempfile
import threading
import time
import unittest
from datetime import datetime
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.request import urlopen

spec = importlib.util.spec_from_file_location("locale_app", Path(__file__).parents[1] / "app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
app = app.backend


class LocalizationTests(unittest.TestCase):
    def test_notification_uses_ha_timezone_then_country_fallback(self):
        app.save_options_file({"country": "gb", "language": "en"})
        reminder = {"id": "uk", "channel": "BBC One", "title": "Evening news", "language": "en",
                    "start": "2030-07-01T18:15:00+00:00"}
        cases = [({}, "19:15"), ({"time_zone": "Europe/London"}, "19:15"),
                 ({"time_zone": "Europe/Berlin"}, "20:15"),
                 ({"time_zone": "invalid", "country": "GB"}, "19:15"),
                 ({"country": "DE"}, "20:15")]
        for locale, wanted in cases:
            with self.subTest(locale=locale), patch.object(app, "home_assistant_locale", return_value=locale), \
                    patch.dict(app.os.environ, {"SUPERVISOR_TOKEN": "test"}), \
                    patch.object(app, "urlopen", return_value=MagicMock()) as send:
                app._ha_notification(reminder)
                self.assertIn(wanted, json.loads(send.call_args.args[0].data)["message"])

    def test_reminder_worker_waits_for_elapsed_minutes_during_repeated_hour(self):
        reminder = {"id": "dst", "channel": "BBC One", "title": "After clock change",
                    "start": "2030-10-27T02:05:00+01:00", "end": "2030-10-27T03:00:00+01:00", "minutes": 10}
        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return current.astimezone(tz)
        for instant, expected in [("2030-10-27T02:00:00+02:00", False),
                                  ("2030-10-27T02:55:00+02:00", True)]:
            current = datetime.fromisoformat(instant)
            with self.subTest(instant=instant), patch.object(app, "datetime", Clock), \
                    patch.object(app, "load_reminders", return_value=[dict(reminder)]), \
                    patch.object(app, "save_reminders"), patch.object(app, "_ha_notification") as send, \
                    patch.object(app.time, "sleep", side_effect=InterruptedError):
                with self.assertRaises(InterruptedError):
                    app.reminder_worker()
                self.assertEqual(send.called, expected)

    def test_guide_does_not_wait_for_slow_core_locale_and_shares_one_refresh(self):
        entered, release = threading.Event(), threading.Event()
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"language":"nl","country":"NL"}'

        def slow_core(request, **kwargs):
            entered.set()
            if not release.wait(3):
                raise TimeoutError("Core deliberately delayed")
            return response

        store = app.EPGStore("de")
        with patch.dict(app.os.environ, {"SUPERVISOR_TOKEN": "test"}), \
                patch.object(app, "urlopen", side_effect=slow_core) as core, \
                patch.object(app, "STORE", store), patch.object(store, "ensure_fresh_async"):
            server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                started = time.monotonic()
                for _ in range(3):
                    with urlopen(f"http://127.0.0.1:{server.server_port}/api/guide", timeout=0.7) as reply:
                        guide = json.load(reply)
                    self.assertEqual(guide["country"], "de")
                self.assertLess(time.monotonic() - started, 1)
                self.assertTrue(entered.wait(1))
                self.assertEqual(core.call_count, 1)
                self.assertFalse(release.is_set())
            finally:
                release.set()
                # The synchronous caller waits for the same worker, without a second request.
                locale = app.home_assistant_locale()
                server.shutdown()
                server.server_close()
            self.assertEqual(locale, {"language": "nl", "country": "NL"})
            self.assertEqual(core.call_count, 1)

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
        for country, expected in [("de", "de"), ("at", "de"), ("nl", "nl"), ("ch", "en"), ("be", "en"), ("no", "nb"), ("gb", "en")]:
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
        response.__enter__.return_value.read.return_value = json.dumps({"language": "nl", "country": "NL", "time_zone": "Europe/Amsterdam", "latitude": 52, "longitude": 4}).encode()
        with patch.dict(app.os.environ, {"SUPERVISOR_TOKEN": "test"}), patch.object(app, "urlopen", return_value=response) as request:
            self.assertEqual(app.home_assistant_locale(), {"language": "nl", "country": "NL", "time_zone": "Europe/Amsterdam"})
            self.assertEqual(app.home_assistant_locale(), {"language": "nl", "country": "NL", "time_zone": "Europe/Amsterdam"})
            request.assert_called_once()
            self.assertEqual(request.call_args.args[0].full_url, "http://supervisor/core/api/config")
            self.assertEqual(request.call_args.kwargs["timeout"], 3)

    def test_danish_settings_profile_country_and_notifications(self):
        app.save_options_file({"country": "dk", "language": "da"})
        self.assertEqual(app.load_options()["language"], "da")
        self.assertEqual(app.effective_language(), "da")
        self.assertEqual(app.translate("Speichern", "da"), "Gem")
        app.save_options_file({"country": "dk", "language": "auto"})
        with patch.object(app, "home_assistant_locale", return_value={}):
            self.assertEqual(app.effective_language(), "da")
        with patch.object(app, "home_assistant_locale", return_value={"language": "da-DK"}):
            self.assertEqual(app.effective_language(), "da")
        reminder = {"id": "danish", "channel": "DR1", "title": "Nyheder", "start": "2030-01-01T20:15:00+01:00", "language": "da"}
        with patch.dict(app.os.environ, {"SUPERVISOR_TOKEN": "test"}), patch.object(app, "urlopen", return_value=MagicMock()) as request:
            app._ha_notification(reminder)
        body = json.loads(request.call_args.args[0].data)
        self.assertIn("Påmindelse", body["title"])
        self.assertIn("Nyheder", body["message"])

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
