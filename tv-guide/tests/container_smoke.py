"""Run against the built container via stdin, without external programme sources."""
import json
import tempfile
import threading
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

import app

backend = app.backend
assert backend.BASE == Path("/app")
assert backend.EPGStore.runtime is backend.Handler.runtime is backend
assert (backend.WWW / "index.html").is_file()
assert (backend.WWW / "channel-picker.js").is_file()
assert (backend.BASE / "data" / "logo_library.json").is_file()
assert (backend.BASE / "lovelace" / "tv-guide-card.js").is_file()

with tempfile.TemporaryDirectory() as folder:
    backend.PARSED_CACHE_FILE = Path(folder) / "parsed.json"
    backend.OPTIONS_FILE = Path(folder) / "options.json"
    backend.CHANNEL_PREFS_FILE = Path(folder) / "order.json"
    store = backend.EPGStore()
    now = datetime.now(backend.EPG_TIMEZONE)
    store.channels[0]["available"] = True
    store.channels[0]["programs"] = [{
        "title": "Container programme",
        "start": now.isoformat(),
        "end": (now + timedelta(hours=1)).isoformat(),
    }]
    store._save_parsed_cache("container-test")
    restored = backend.EPGStore()
    assert restored.channels[0]["programs"][0]["title"] == "Container programme"
    restored.ensure_fresh_async = lambda: None
    backend.STORE = restored
    austrian = backend.EPGStore("at")
    austrian.ensure_fresh_async = lambda: None
    backend.COUNTRY_STORES = {"de": restored, "at": austrian}

    server = ThreadingHTTPServer(("127.0.0.1", 0), backend.Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        with urlopen(base + "/", timeout=5) as response:
            assert response.status == 200
            assert b"guide-core.js" in response.read()
        with urlopen(base + "/api/settings", timeout=5) as response:
            assert json.loads(response.read())["country"] == "de"
        with urlopen(base + "/api/guide", timeout=5) as response:
            guide = json.loads(response.read())
            assert guide["country"] == "de"
            assert any(p["title"] == "Container programme"
                       for channel in guide["channels"] for p in channel["programs"])
        with urlopen(base + "/api/personal-channels", timeout=5) as response:
            personal = json.loads(response.read())
            assert {item["code"] for item in personal["supported_countries"]} == set(backend.COUNTRIES)
            assert "fr" in {item["code"] for item in personal["supported_countries"]}
            assert any(item["id"] == "fr:fr_tf1" for item in personal["channels"])
        keys = ["de:" + restored.channels[0]["id"], "at:" + austrian.channels[0]["id"]]
        request = Request(base + "/api/personal-channels", data=json.dumps({"order": keys, "countries": []}).encode(),
                          headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=5) as response:
            assert json.loads(response.read())["ok"]
        with urlopen(base + "/api/guide", timeout=5) as response:
            assert json.loads(response.read())["custom_channel_ids"] == keys
        assert backend.PersonalChannels(backend).load(austrian)["order"] == keys
    finally:
        server.shutdown()
        server.server_close()
        worker.join(5)

print("Container backend, resources, cache restart and HTTP endpoints passed")
