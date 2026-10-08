"""Optional state publishing must not block the guide or overwrite foreign states."""
import importlib.util
import json
import tempfile
import threading
import unittest
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

spec = importlib.util.spec_from_file_location("sensor_app", Path(__file__).parents[1] / "app.py")
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)
app = entry.backend
from tvguide.ha_sensors import SENSOR_OPTIONS, SensorPublisher


class SensorTests(unittest.TestCase):
    def test_next_reminder_uses_elapsed_minutes_across_autumn_clock_change(self):
        app.save_reminders([{"id": "dst", "start": "2030-10-27T02:05:00+01:00",
                             "end": "2030-10-27T03:00:00+01:00", "minutes": 10}])
        values = self.publisher._values(datetime.fromisoformat("2030-10-27T02:00:00+02:00"))
        due = datetime.fromisoformat(values["sensor_next_reminder"][0])
        self.assertEqual(due, datetime.fromisoformat("2030-10-27T00:55:00+00:00"))

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        root = Path(folder.name)
        patches = patch.multiple(app, OPTIONS_FILE=root / "options.json",
                                 REMINDERS_FILE=root / "reminders.json", BOOKMARKS_FILE=root / "bookmarks.json",
                                 STORE=SimpleNamespace(last_loaded=None, refresh_running=False))
        patches.start()
        self.addCleanup(patches.stop)
        token = patch.dict(app.os.environ, {"SUPERVISOR_TOKEN": "test"})
        token.start()
        self.addCleanup(token.stop)
        self.states, self.requests = {}, []
        opener = patch.object(app, "urlopen", side_effect=self.core)
        opener.start()
        self.addCleanup(opener.stop)
        app.save_options_file({"language": "en"})
        self.publisher = SensorPublisher(app)

    def core(self, request, **kwargs):
        entity_id = request.full_url.rsplit("/", 1)[-1]
        method = request.get_method()
        self.requests.append((method, entity_id))
        self.assertEqual(kwargs["timeout"], 3)
        if method == "POST":
            self.states[entity_id] = json.loads(request.data)
        elif method == "DELETE":
            self.states.pop(entity_id, None)
        elif entity_id not in self.states:
            raise HTTPError(request.full_url, 404, "Not found", {}, None)
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(self.states.get(entity_id, {})).encode()
        return response

    def enable(self, **settings):
        app.save_options_file({"language": "en", **settings})

    def test_disabled_by_default_does_not_contact_core(self):
        self.assertFalse(any(app.load_options()[key] for key in SENSOR_OPTIONS))
        self.publisher.publish_once()
        self.assertEqual(self.requests, [])
        self.assertFalse(self.publisher.path.exists())

    def test_values_exclude_sent_expired_and_invalid_entries(self):
        now = datetime.now(app.EPG_TIMEZONE)
        start, end = now + timedelta(hours=1), now + timedelta(hours=2)
        reminder = {"id": "next", "channel": "Sender", "channelId": "de:ard", "title": "Programme",
                    "start": start.isoformat(), "end": end.isoformat(), "minutes": 10}
        app.save_reminders([reminder, {**reminder, "sent": True}, {**reminder, "start": (now - timedelta(hours=1)).isoformat()}, None])
        app.save_bookmarks([{**reminder}, {"end": (now - timedelta(hours=1)).isoformat()}, None])
        app.STORE.last_loaded = now.isoformat()
        app.STORE.refresh_running = True
        self.enable(**{key: True for key in SENSOR_OPTIONS})
        self.publisher.publish_once()
        self.assertEqual(len(self.states), 5)
        self.assertEqual(self.states["sensor.tv_guide_bookmark_count"]["state"], "1")
        self.assertEqual(self.states["sensor.tv_guide_reminder_count"]["state"], "1")
        self.assertEqual(self.states["binary_sensor.tv_guide_refresh_running"]["state"], "on")
        next_state = self.states["sensor.tv_guide_next_reminder"]
        self.assertEqual(next_state["state"], (start - timedelta(minutes=10)).isoformat())
        self.assertEqual(next_state["attributes"]["programme_start"], start.isoformat())
        self.assertEqual(next_state["attributes"]["device_class"], "timestamp")
        self.assertEqual(self.states["sensor.tv_guide_last_update"]["state"], now.isoformat())

    def test_empty_timestamps_and_independent_selection(self):
        self.enable(sensor_next_reminder=True, sensor_last_update=True)
        self.publisher.publish_once()
        self.assertEqual(set(self.states), {"sensor.tv_guide_next_reminder", "sensor.tv_guide_last_update"})
        self.assertTrue(all(state["state"] == "unknown" for state in self.states.values()))

    def test_unchanged_states_are_quiet_and_core_restart_is_reconciled(self):
        self.enable(sensor_bookmark_count=True)
        with patch("tvguide.ha_sensors.time.monotonic", return_value=10) as clock:
            self.publisher.publish_once()
            self.requests.clear()
            clock.return_value = 69
            self.publisher.publish_once()
            self.assertEqual(self.requests, [])
            self.states.clear()  # Home Assistant restarted, while the add-on stayed running.
            clock.return_value = 70
            self.publisher.publish_once()
            self.assertEqual(self.states["sensor.tv_guide_bookmark_count"]["state"], "0")
        self.requests.clear()
        self.publisher.checked_at = {}
        with patch("tvguide.ha_sensors.time.monotonic", return_value=1):
            self.publisher.publish_once()
        self.assertEqual(self.requests, [("GET", "sensor.tv_guide_bookmark_count")])

    def test_disabling_after_addon_restart_removes_only_owned_states(self):
        self.enable(sensor_bookmark_count=True)
        self.publisher.publish_once()
        self.enable()
        restarted = SensorPublisher(app)
        restarted.publish_once()
        self.assertEqual(self.states, {})
        self.assertEqual(json.loads(restarted.path.read_text()), [])
        self.assertIn(("DELETE", "sensor.tv_guide_bookmark_count"), self.requests)

    def test_foreign_state_is_neither_overwritten_nor_deleted(self):
        entity_id = "sensor.tv_guide_bookmark_count"
        foreign = {"state": "42", "attributes": {"friendly_name": "User sensor"}}
        self.states[entity_id] = foreign
        self.enable(sensor_bookmark_count=True)
        self.publisher.publish_once()
        self.assertEqual(self.states[entity_id], foreign)
        self.publisher._manage(entity_id, True)  # A former owned sensor was replaced by the user.
        self.enable()
        self.publisher.publish_once()
        self.assertEqual(self.states[entity_id], foreign)
        self.assertFalse(any(method in {"POST", "DELETE"} for method, _ in self.requests))

    def test_core_failure_retries_without_losing_cleanup_after_restart(self):
        self.enable(sensor_bookmark_count=True)
        with patch.object(app, "urlopen", side_effect=TimeoutError("Core unavailable")):
            self.publisher.publish_once()
        self.publisher.publish_once()
        self.enable()
        with patch.object(app, "urlopen", side_effect=TimeoutError("Core unavailable")):
            self.publisher.publish_once()
        self.assertIn("sensor.tv_guide_bookmark_count", self.publisher.managed)
        SensorPublisher(app).publish_once()
        self.assertEqual(self.states, {})

    def test_disabling_during_core_lookup_does_not_create_state(self):
        self.enable(sensor_bookmark_count=True)
        def changed(request, **kwargs):
            self.enable()
            return self.core(request, **kwargs)
        with patch.object(app, "urlopen", side_effect=changed):
            self.publisher.publish_once()
        self.assertEqual(self.states, {})

    def test_slow_core_publisher_does_not_block_http_guide(self):
        entered, release = threading.Event(), threading.Event()
        self.enable(sensor_bookmark_count=True)
        store = app.EPGStore("de")
        def slow(request, **kwargs):
            entered.set()
            release.wait(3)
            return self.core(request, **kwargs)
        with patch.object(app, "STORE", store), patch.object(store, "ensure_fresh_async"), \
                patch.object(app, "home_assistant_locale", return_value={}), patch.object(app, "urlopen", side_effect=slow):
            worker = threading.Thread(target=self.publisher.publish_once)
            worker.start()
            server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                self.assertTrue(entered.wait(1))
                with urlopen(f"http://127.0.0.1:{server.server_port}/api/guide", timeout=0.7) as response:
                    self.assertEqual(json.load(response)["country"], "de")
                self.assertFalse(release.is_set())
            finally:
                release.set()
                worker.join(3)
                server.shutdown()
                server.server_close()
            self.assertFalse(worker.is_alive())

    def test_settings_api_persists_checks_preserves_legacy_clients_and_rejects_strings(self):
        with patch.object(app, "STORE", app.EPGStore("de")), patch.object(app, "update_addon_options") as supervisor:
            server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                url = f"http://127.0.0.1:{server.server_port}/api/settings"
                with urlopen(url) as response:
                    settings = json.load(response)
                settings.update(sensor_bookmark_count=True, sensor_last_update=True)
                def post(value):
                    return urlopen(Request(url, data=json.dumps(value).encode(), headers={"Content-Type": "application/json"}))
                with post(settings) as response:
                    self.assertTrue(json.load(response)["ok"])
                self.assertTrue(supervisor.call_args.args[0]["sensor_bookmark_count"])
                with post({key: value for key, value in settings.items() if key not in SENSOR_OPTIONS}):
                    pass
                self.assertTrue(app.load_options()["sensor_bookmark_count"])
                with self.assertRaises(HTTPError) as error:
                    post({**settings, "sensor_bookmark_count": "false"})
                self.assertEqual(error.exception.code, 400)
                self.assertEqual(supervisor.call_count, 2)
                with urlopen(url) as response:
                    self.assertTrue(json.load(response)["sensor_last_update"])
            finally:
                server.shutdown()
                server.server_close()
