from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime, timedelta
import json
import os

BASE = Path(__file__).resolve().parent
WWW = BASE / "www"
CHANNELS = json.loads((BASE / "data" / "channels.json").read_text(encoding="utf-8"))

SAMPLES = {
    "ard": ["Tagesschau", "Wer weiß denn sowas?", "Großstadtrevier", "Tagesthemen", "Tatort"],
    "zdf": ["Die Rosenheim-Cops", "heute", "Wetter", "SOKO", "heute journal"],
    "rtl": ["RTL Aktuell", "Explosiv", "Gute Zeiten, schlechte Zeiten", "Show am Abend", "Nachtjournal"],
    "sat1": ["Auf den Punkt", "SAT.1 :newstime", "Spielfilm", "Reportage", "Nachrichten"],
    "prosieben": ["taff", "ProSieben :newstime", "Galileo", "Prime-Time-Show", "Late Night"],
    "kabeleins": ["Abenteuer Leben", "Mein Lokal, Dein Lokal", "Achtung Kontrolle!", "Spielfilm", "Navy CIS"],
    "rtlzwei": ["RTLZWEI News", "Berlin - Tag & Nacht", "Hartz und herzlich", "Realityshow", "Dokusoap"],
    "vox": ["Shopping Queen", "First Dates", "Das perfekte Dinner", "Spielfilm", "Medical Detectives"],
    "arte": ["Stadt Land Kunst", "ARTE Journal", "Re:", "Dokumentarfilm", "Kulturmagazin"],
    "3sat": ["Kulturzeit", "nano", "ZIB", "Dokumentation", "Spielfilm"],
}

def demo_programs(channel_id):
    now = datetime.now().replace(second=0, microsecond=0)
    start = now - timedelta(minutes=23)
    titles = SAMPLES.get(channel_id, ["Magazin", "Nachrichten", "Dokumentation", "Abendprogramm", "Nachtprogramm"])
    durations = [55, 30, 60, 110, 60, 55]
    out = []
    t = start
    for i in range(6):
        dur = durations[i % len(durations)]
        end = t + timedelta(minutes=dur)
        out.append({
            "title": titles[i % len(titles)],
            "start": t.isoformat(),
            "end": end.isoformat(),
            "subtitle": ""
        })
        t = end
    return out

def guide_payload():
    rows = []
    for ch in CHANNELS["channels"]:
        rows.append({**ch, "programs": demo_programs(ch["id"])})
    return {
        "generated_at": datetime.now().isoformat(),
        "profile": CHANNELS["profile"],
        "group": CHANNELS["group"],
        "channels": rows
    }

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        raw = urlparse(path).path
        rel = raw.lstrip("/") or "index.html"
        return str(WWW / rel)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.rstrip("/").endswith("/api/guide") or parsed.path == "/api/guide":
            payload = json.dumps(guide_payload(), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if parsed.path.rstrip("/").endswith("/api/channels") or parsed.path == "/api/channels":
            payload = json.dumps(CHANNELS, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        return super().do_GET()

    def log_message(self, fmt, *args):
        print("[TV Guide]", fmt % args, flush=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8099"))
    print(f"[TV Guide] Start auf Port {port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
