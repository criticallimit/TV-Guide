"""Deployment paths and shared application state after backend modularisation."""
import importlib.util
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.request import urlopen

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("backend_entry", ROOT / "app.py")
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)
app = entry.backend


class BackendStructureTests(unittest.TestCase):
    def test_store_and_handler_share_application_context(self):
        self.assertIs(app.EPGStore.runtime, app)
        self.assertIs(app.Handler.runtime, app)
        self.assertIs(app.STORE.runtime, app.Handler.runtime)

    def test_resource_paths_still_point_to_addon_root(self):
        self.assertEqual(app.BASE, ROOT)
        self.assertEqual(app.WWW, ROOT / "www")
        self.assertTrue((app.BASE / "data" / "countries.json").is_file())

    def test_cache_paths_remain_country_specific_after_context_change(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "parsed.json"
            de = app.EPGStore.__new__(app.EPGStore)
            no = app.EPGStore.__new__(app.EPGStore)
            no._country = "no"
            with patch.object(app, "PARSED_CACHE_FILE", path):
                self.assertEqual(de.parsed_cache_file, path)
                self.assertNotEqual(no.parsed_cache_file, path)
                self.assertEqual(no.parsed_cache_file.parent, path.parent)

    def test_container_copies_backend_package(self):
        dockerfile = (ROOT / "Dockerfile").read_text()
        self.assertIn("COPY tvguide /app/tvguide", dockerfile)
        self.assertTrue((ROOT / "tvguide" / "services.py").is_file())

    def test_startup_serves_requests_while_refresh_waits(self):
        refresh_started = threading.Event()
        release_refresh = threading.Event()
        servers = []

        def server_factory(address, handler):
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            servers.append(server)
            return server

        def refresh():
            refresh_started.set()
            release_refresh.wait(5)

        with patch.object(app, "ThreadingHTTPServer", side_effect=server_factory), \
                patch.object(app.STORE, "refresh", side_effect=refresh), \
                patch.object(app, "reminder_worker"), \
                patch.object(app.SENSOR_PUBLISHER, "run"), \
                patch.object(app.STORE, "refresh_running", False):
            thread = threading.Thread(target=app.main, daemon=True)
            thread.start()
            try:
                self.assertTrue(refresh_started.wait(3))
                server = servers[0]
                with urlopen(f"http://127.0.0.1:{server.server_port}/api/settings", timeout=3) as response:
                    self.assertEqual(response.status, 200)
                    self.assertIn("country", json.loads(response.read()))
                self.assertFalse(release_refresh.is_set())
            finally:
                release_refresh.set()
                for server in servers:
                    server.shutdown()
                    server.server_close()
                thread.join(3)


if __name__ == "__main__":
    unittest.main()
