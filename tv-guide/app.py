from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import xml.etree.ElementTree as ET
import threading
import json
import gzip
import io
import os
import re
import time
import unicodedata

BASE = Path(__file__).resolve().parent
WWW = BASE / "www"
CHANNELS = json.loads((BASE / "data" / "channels.json").read_text(encoding="utf-8"))
OPTIONS_FILE = Path("/data/options.json")
CACHE_FILE = Path("/data/tv_guide_epg.xml.gz")
STATE_FILE = Path("/data/tv_guide_epg_state.json")

DEFAULT_EPG_URL = "https://iptv-org.github.io/epg/guides/de/hd-plus.de.epg.xml"
LEGACY_EPG_URL = "https://www.free-epg.de/api/epg/de.xml.gz"
DEFAULT_REFRESH_MINUTES = 180

def load_options():
    try:
        data = json.loads(OPTIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    url = str(data.get("epg_url") or DEFAULT_EPG_URL).strip()
    # Migrate the old built-in FreeEPG default automatically; user-defined URLs remain untouched.
    if url == LEGACY_EPG_URL:
        url = DEFAULT_EPG_URL
    refresh = int(data.get("refresh_minutes") or DEFAULT_REFRESH_MINUTES)
    if not url.startswith(("http://", "https://")):
        url = DEFAULT_EPG_URL
    return {
        "epg_url": url,
        "refresh_minutes": max(30, min(1440, refresh)),
    }

def normalize(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = value.lower().replace("&", "und")
    value = re.sub(r"\b(hd|uhd|sd)\b", "", value)
    return re.sub(r"[^a-z0-9]+", "", value)

def xmltv_datetime(value):
    value = (value or "").strip()
    if not value:
        return None
    m = re.match(r"^(\d{8,14})(?:\s*([+-]\d{4}|Z))?", value)
    if not m:
        return None
    base, offset = m.groups()
    # XMLTV permits reduced precision; pad missing time fields with zeros.
    base = (base + "000000")[0:14]
    dt = datetime.strptime(base, "%Y%m%d%H%M%S")
    if offset == "Z":
        dt = dt.replace(tzinfo=timezone.utc)
    elif offset:
        sign = 1 if offset[0] == "+" else -1
        hours = int(offset[1:3])
        minutes = int(offset[3:5])
        dt = dt.replace(tzinfo=timezone(sign * timedelta(hours=hours, minutes=minutes)))
    else:
        dt = dt.astimezone()
    return dt.astimezone()

def first_text(node, tag):
    child = node.find(tag)
    return (child.text or "").strip() if child is not None and child.text else ""

class EPGStore:
    def __init__(self):
        self.lock = threading.Lock()
        self.options = load_options()
        self.channels = [{
            **ch,
            "available": False,
            "programs": [],
            "source_name": None,
            "source_id": None,
            "logo": None,
        } for ch in sorted(CHANNELS["channels"], key=lambda x: x["order"])]
        self.last_error = None
        self.last_loaded = None
        self.source_updated = None
        self.refresh_running = False
        self.feed_latest_end = None

    def _load_state(self):
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_state(self):
        payload = {
            "source_url": self.options["epg_url"],
            "downloaded_at": datetime.now().astimezone().isoformat(),
        }
        STATE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _cache_fresh(self):
        if not CACHE_FILE.exists():
            return False

        state = self._load_state()
        cached_source = str(state.get("source_url") or "").strip()
        current_source = str(self.options["epg_url"] or "").strip()

        if cached_source != current_source:
            print(
                f"[TV Guide] EPG-Quelle geändert: Cache wird verworfen "
                f"({cached_source or 'unbekannt'} -> {current_source})",
                flush=True,
            )
            return False

        age = time.time() - CACHE_FILE.stat().st_mtime
        return age < self.options["refresh_minutes"] * 60

    def _download(self):
        url = self.options["epg_url"]
        req = Request(url, headers={
            "User-Agent": "HomeAssistant-TV-Guide/0.2.0",
            "Accept-Encoding": "gzip",
        })
        with urlopen(req, timeout=45) as response:
            raw = response.read(100 * 1024 * 1024 + 1)
            if len(raw) > 100 * 1024 * 1024:
                raise ValueError("EPG-Datei ist größer als 100 MB.")
            encoding = (response.headers.get("Content-Encoding") or "").lower()
            ctype = (response.headers.get("Content-Type") or "").lower()
            if encoding == "gzip" and not raw.startswith(b"\x1f\x8b"):
                raw = gzip.compress(raw)
            elif not raw.startswith(b"\x1f\x8b") and "gzip" not in ctype and not url.endswith(".gz"):
                raw = gzip.compress(raw)
        tmp = CACHE_FILE.with_suffix(".tmp")
        tmp.write_bytes(raw)
        os.replace(tmp, CACHE_FILE)
        self.source_updated = datetime.now().astimezone().isoformat()
        self._save_state()
        print(f"[TV Guide] Neuer EPG-Feed geladen: {url}", flush=True)

    def _open_xml(self):
        raw = CACHE_FILE.read_bytes()
        if raw.startswith(b"\x1f\x8b"):
            return gzip.GzipFile(fileobj=io.BytesIO(raw))
        return io.BytesIO(raw)

    def _build_channel_map(self):
        wanted = {}
        for ch in CHANNELS["channels"]:
            keys = {normalize(ch["name"]), normalize(ch["id"])}
            keys.update(normalize(a) for a in ch.get("aliases", []))
            keys.update(normalize(a) for a in ch.get("xmltv_ids", []))
            wanted[ch["id"]] = {k for k in keys if k}

        channel_meta = {}
        with self._open_xml() as fh:
            for event, elem in ET.iterparse(fh, events=("end",)):
                if elem.tag != "channel":
                    continue
                cid = elem.attrib.get("id", "")
                names = [(x.text or "").strip() for x in elem.findall("display-name") if x.text]
                icon = elem.find("icon")
                icon_url = icon.attrib.get("src") if icon is not None else None
                source_keys = [normalize(cid)] + [normalize(x) for x in names]
                best = None
                best_score = -1
                for internal_id, keys in wanted.items():
                    for skey in source_keys:
                        if not skey:
                            continue
                        if skey in keys:
                            score = 1000 + len(skey)
                        else:
                            score = max(
                                [len(k) for k in keys if len(k) >= 4 and (skey.startswith(k) or k.startswith(skey))] or [-1]
                            )
                        if score > best_score:
                            best_score = score
                            best = internal_id
                if best and best not in channel_meta:
                    channel_meta[best] = {
                        "xmltv_id": cid,
                        "display_name": names[0] if names else cid,
                        "icon": icon_url,
                    }
                elem.clear()
        return channel_meta

    def _parse(self):
        channel_meta = self._build_channel_map()
        xml_to_internal = {
            meta["xmltv_id"]: internal_id for internal_id, meta in channel_meta.items()
        }
        programmes = {ch["id"]: [] for ch in CHANNELS["channels"]}
        seen_programmes = 0
        matched_programmes = 0
        first_start = None
        last_start = None
        latest_end = None

        with self._open_xml() as fh:
            for event, elem in ET.iterparse(fh, events=("end",)):
                if elem.tag != "programme":
                    continue
                seen_programmes += 1
                source_id = elem.attrib.get("channel", "")
                internal_id = xml_to_internal.get(source_id)
                if not internal_id:
                    elem.clear()
                    continue

                start = xmltv_datetime(elem.attrib.get("start"))
                end = xmltv_datetime(elem.attrib.get("stop"))
                if not start or not end:
                    elem.clear()
                    continue

                matched_programmes += 1
                first_start = start if first_start is None or start < first_start else first_start
                last_start = start if last_start is None or start > last_start else last_start
                latest_end = end if latest_end is None or end > latest_end else latest_end

                icon = elem.find("icon")
                programmes[internal_id].append({
                    "title": first_text(elem, "title") or "Ohne Titel",
                    "subtitle": first_text(elem, "sub-title"),
                    "desc": first_text(elem, "desc"),
                    "category": first_text(elem, "category"),
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "icon": icon.attrib.get("src") if icon is not None else None,
                })
                elem.clear()

        self.feed_latest_end = latest_end.isoformat() if latest_end else None
        now = datetime.now().astimezone()
        if latest_end and latest_end < now - timedelta(hours=2):
            raise ValueError(
                f"EPG-Feed ist veraltet: letzte Sendung endet am {latest_end.isoformat()}; "
                f"aktuelle Zeit ist {now.isoformat()}."
            )

        print(
            "[TV Guide] XMLTV Diagnose: "
            f"{len(channel_meta)} Sender gemappt, "
            f"{seen_programmes} Programme im Feed, "
            f"{matched_programmes} Programme für unsere Sender"
            + (f", Zeitraum {first_start.isoformat()} bis {last_start.isoformat()}" if first_start and last_start else ""),
            flush=True,
        )

        result = []
        for ch in sorted(CHANNELS["channels"], key=lambda x: x["order"]):
            meta = channel_meta.get(ch["id"], {})
            items = sorted(programmes.get(ch["id"], []), key=lambda x: x["start"])
            result.append({
                **ch,
                "source_name": meta.get("display_name"),
                "source_id": meta.get("xmltv_id"),
                "logo": meta.get("icon"),
                "available": bool(items),
                "programs": items,
            })
        return result

    def refresh(self, force=False):
        with self.lock:
            self.refresh_running = True
            self.options = load_options()
            try:
                cache_fresh = self._cache_fresh()
                if force or not cache_fresh:
                    self._download()
                self.channels = self._parse()
                self.last_loaded = datetime.now().astimezone().isoformat()
                self.last_error = None
                available = sum(1 for ch in self.channels if ch.get("available"))
                print(f"[TV Guide] EPG geladen: {available} von {len(self.channels)} Sendern mit Programmdaten", flush=True)
            except Exception as exc:
                self.last_error = str(exc)
                print(f"[TV Guide] EPG-Fehler: {self.last_error}", flush=True)
                if CACHE_FILE.exists():
                    try:
                        self.channels = self._parse()
                        self.last_loaded = datetime.now().astimezone().isoformat()
                    except Exception:
                        pass
            finally:
                self.refresh_running = False

    def ensure_fresh_async(self):
        if not self._cache_fresh() and not self.refresh_running:
            self.refresh_running = True
            threading.Thread(target=self.refresh, daemon=True).start()

    def payload(self):
        self.ensure_fresh_async()
        return {
            "generated_at": datetime.now().astimezone().isoformat(),
            "profile": CHANNELS["profile"],
            "group": CHANNELS["group"],
            "provider": "XMLTV",
            "source_url": self.options["epg_url"],
            "refresh_minutes": self.options["refresh_minutes"],
            "last_loaded": self.last_loaded,
            "feed_latest_end": self.feed_latest_end,
            "error": self.last_error,
            "channels": self.channels,
        }

STORE = EPGStore()

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        raw = urlparse(path).path
        rel = raw.lstrip("/") or "index.html"
        return str(WWW / rel)

    def _json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path.endswith("/api/guide") or path == "/api/guide":
            return self._json(STORE.payload())
        if path.endswith("/api/channels") or path == "/api/channels":
            return self._json(CHANNELS)
        if path.endswith("/api/status") or path == "/api/status":
            return self._json({
                "provider": "XMLTV",
                "source_url": STORE.options["epg_url"],
                "last_loaded": STORE.last_loaded,
                "feed_latest_end": STORE.feed_latest_end,
                "error": STORE.last_error,
                "cache_exists": CACHE_FILE.exists(),
                "refresh_running": STORE.refresh_running,
            })
        if path.endswith("/api/refresh") or path == "/api/refresh":
            STORE.refresh(force=True)
            return self._json({"ok": STORE.last_error is None, "error": STORE.last_error})
        return super().do_GET()

    def log_message(self, fmt, *args):
        print("[TV Guide]", fmt % args, flush=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8099"))
    print(f"[TV Guide] Webserver startet sofort auf Port {port}", flush=True)
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=STORE.refresh, daemon=True).start()
    print("[TV Guide] Ingress ist bereit; EPG wird im Hintergrund geladen", flush=True)
    server.serve_forever()
