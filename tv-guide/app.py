import gzip
import html
import json
import os
import re
import threading
import time
import unicodedata
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent
WWW = BASE / "www"
CHANNELS = json.loads((BASE / "data" / "channels.json").read_text(encoding="utf-8"))
OPTIONS_FILE = Path("/data/options.json")
CACHE_FILE = Path("/data/tv_guide_epg.xml.gz")
STATE_FILE = Path("/data/tv_guide_epg_state.json")
PARSED_CACHE_FILE = Path("/data/tv_guide_epg_parsed.json")
CHANNEL_PREFS_FILE = Path("/data/tv_guide_channel_order.json")
REMINDERS_FILE = Path("/data/tv_guide_reminders.json")
BOOKMARKS_FILE = Path("/data/tv_guide_bookmarks.json")
REMINDER_LOCK = threading.Lock()
BOOKMARK_LOCK = threading.Lock()

DEFAULT_EPG_URL = "https://epgshare01.online/epgshare01/epg_ripper_DE1.xml.gz"
LEGACY_EPG_URLS = {
    "https://www.free-epg.de/api/epg/de.xml.gz",
    "https://iptv-org.github.io/epg/guides/de/hd-plus.de.epg.xml",
    "https://iptv-org.github.io/epg/guides/de/hd-plus.de.xml",
    "https://raw.githubusercontent.com/PrinzMichiDE/free-epg-germany/main/epg3.xml.gz",
}
FREE_FALLBACK_EPG_URLS = []
ARD_RB_PROGRAM_URL = "https://www.ardmediathek.de/radiobremen/programm/{date}"
DEFAULT_REFRESH_MINUTES = 180

def load_options():
    try:
        data = json.loads(OPTIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    url = str(data.get("epg_url") or DEFAULT_EPG_URL).strip()
    # Migrate previous built-in defaults automatically; user-defined URLs remain untouched.
    if url in LEGACY_EPG_URLS:
        url = DEFAULT_EPG_URL
    try:
        refresh = int(data.get("refresh_minutes") or DEFAULT_REFRESH_MINUTES)
    except Exception:
        refresh = DEFAULT_REFRESH_MINUTES
    notification_service = str(data.get("notification_service") or "persistent_notification.create").strip().lower()
    if not re.match(r"^[a-z0-9_]+\.[a-z0-9_]+$", notification_service):
        notification_service = "persistent_notification.create"
    if not url.startswith(("http://", "https://")):
        url = DEFAULT_EPG_URL
    return {
        "epg_url": url,
        "refresh_minutes": max(30, min(1440, refresh)),
        "notification_service": notification_service,
    }

def load_options_ui():
    try:
        data = json.loads(OPTIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    default_view = str(data.get("default_view") or "now")
    if default_view not in {"now", "2015", "2200"}:
        default_view = "now"
    try:
        columns = int(data.get("columns_desktop") or 5)
    except Exception:
        columns = 5
    try:
        max_channels = int(data.get("max_channels") or 0)
    except Exception:
        max_channels = 0
    theme_mode = str(data.get("theme_mode") or "auto").lower()
    if theme_mode not in {"auto", "dark", "light"}:
        theme_mode = "auto"
    return {
        "default_view": default_view,
        "columns_desktop": max(3, min(6, columns)),
        "max_channels": max(0, min(38, max_channels)),
        "theme_mode": theme_mode,
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

def base_channel_ids():
    return [ch["id"] for ch in sorted(CHANNELS["channels"], key=lambda x: x["order"])]

def merge_channel_order(saved_order):
    base = base_channel_ids()
    known = set(base)
    order = []
    for channel_id in saved_order or []:
        if channel_id in known and channel_id not in order:
            order.append(channel_id)

    # New channels are inserted near their default-order neighbours instead of
    # destroying an existing user-defined order.
    for channel_id in base:
        if channel_id in order:
            continue
        base_index = base.index(channel_id)
        following = next((x for x in base[base_index + 1:] if x in order), None)
        if following:
            order.insert(order.index(following), channel_id)
            continue
        preceding = next((x for x in reversed(base[:base_index]) if x in order), None)
        if preceding:
            order.insert(order.index(preceding) + 1, channel_id)
        else:
            order.append(channel_id)
    return order

def load_channel_preferences():
    try:
        raw = json.loads(CHANNEL_PREFS_FILE.read_text(encoding="utf-8"))
    except Exception:
        raw = {}
    order = merge_channel_order(raw.get("order"))
    known = set(base_channel_ids())
    hidden = [x for x in raw.get("hidden", []) if x in known]
    return {"order": order, "hidden": hidden}

def save_channel_preferences(order, hidden):
    prefs = {
        "order": merge_channel_order(order),
        "hidden": [x for x in hidden if x in set(base_channel_ids())],
    }
    tmp = CHANNEL_PREFS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(prefs, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, CHANNEL_PREFS_FILE)
    return prefs

def reset_channel_preferences():
    try:
        CHANNEL_PREFS_FILE.unlink()
    except FileNotFoundError:
        pass
    return {"order": base_channel_ids(), "hidden": []}

def ordered_visible_channels(channels):
    prefs = load_channel_preferences()
    by_id = {ch["id"]: ch for ch in channels}
    hidden = set(prefs["hidden"])
    return [by_id[channel_id] for channel_id in prefs["order"] if channel_id in by_id and channel_id not in hidden]

def load_reminders():
    try:
        data = json.loads(REMINDERS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []

def save_reminders(items):
    tmp = REMINDERS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, REMINDERS_FILE)

def load_bookmarks():
    try:
        data = json.loads(BOOKMARKS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []

def save_bookmarks(items):
    tmp = BOOKMARKS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, BOOKMARKS_FILE)

def clean_bookmarks(items):
    now = datetime.now().astimezone()
    result = []
    for item in items:
        try:
            end = datetime.fromisoformat(str(item.get("end") or "")).astimezone()
        except Exception:
            continue
        if end > now:
            result.append(item)
    return result

def update_addon_options(options):
    token = os.environ.get("SUPERVISOR_TOKEN", "")
    if not token:
        raise RuntimeError("Supervisor-API-Token fehlt.")

    payload = json.dumps({"options": options}, ensure_ascii=False).encode("utf-8")
    req = Request(
        "http://supervisor/addons/self/options",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urlopen(req, timeout=10) as response:
        raw = response.read(64 * 1024)
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f"Supervisor hat HTTP {response.status} zurückgegeben.")
        if raw:
            result = json.loads(raw.decode("utf-8"))
            if isinstance(result, dict) and result.get("result") not in {None, "ok"}:
                raise RuntimeError(str(result))

def list_notification_services():
    services = [{
        "service": "persistent_notification.create",
        "label": "Home Assistant",
        "type": "home_assistant",
    }]

    token = os.environ.get("SUPERVISOR_TOKEN", "")
    if not token:
        return services

    req = Request(
        "http://supervisor/core/api/services",
        method="GET",
        headers={"Authorization": f"Bearer {token}"},
    )

    try:
        with urlopen(req, timeout=10) as response:
            raw = response.read(2 * 1024 * 1024)
            payload = json.loads(raw.decode("utf-8"))

        notify_domain = next(
            (
                item for item in payload
                if isinstance(item, dict) and item.get("domain") == "notify"
            ),
            None,
        )
        notify_services = notify_domain.get("services", {}) if isinstance(notify_domain, dict) else {}

        mobile = []
        for service_name in notify_services:
            if not str(service_name).startswith("mobile_app_"):
                continue
            device = str(service_name)[len("mobile_app_"):].replace("_", " ").strip()
            if device:
                device = device[0].upper() + device[1:]
            else:
                device = str(service_name)
            mobile.append({
                "service": f"notify.{service_name}",
                "label": f"Mobilgerät · {device}",
                "type": "mobile_app",
            })

        mobile.sort(key=lambda item: item["label"].casefold())
        services.extend(mobile)
    except Exception as exc:
        print(f"[TV Guide] Benachrichtigungsziele konnten nicht gelesen werden: {exc}", flush=True)

    return services

def _ha_notification(reminder):
    token = os.environ.get("SUPERVISOR_TOKEN", "")
    if not token:
        raise RuntimeError("Home-Assistant-API-Token fehlt.")

    options = load_options()
    service = options.get("notification_service", "persistent_notification.create")
    domain, service_name = service.split(".", 1)

    start = datetime.fromisoformat(reminder["start"]).astimezone()
    message = (
        f'{reminder["channel"]}: „{reminder["title"]}“ beginnt um '
        f'{start.strftime("%H:%M")} Uhr.'
    )
    body = {
        "title": "TV Guide – Erinnerung",
        "message": message,
    }
    if domain == "persistent_notification" and service_name == "create":
        body["notification_id"] = (
            "tv_guide_" + re.sub(r"[^a-zA-Z0-9_]+", "_", reminder["id"])[-180:]
        )

    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = Request(
        f"http://supervisor/core/api/services/{domain}/{service_name}",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urlopen(req, timeout=10) as response:
        response.read(1024)

def reminder_worker():
    while True:
        try:
            now = datetime.now().astimezone()
            changed = False
            with REMINDER_LOCK:
                reminders = load_reminders()
                kept = []
                for reminder in reminders:
                    try:
                        start = datetime.fromisoformat(reminder["start"]).astimezone()
                        end = datetime.fromisoformat(reminder["end"]).astimezone()
                        minutes = max(0, min(180, int(reminder.get("minutes", 10))))
                    except Exception:
                        changed = True
                        continue

                    if end < now - timedelta(hours=1):
                        changed = True
                        continue

                    trigger_at = start - timedelta(minutes=minutes)
                    if not reminder.get("sent") and trigger_at <= now < start + timedelta(minutes=5):
                        try:
                            _ha_notification(reminder)
                            reminder["sent"] = True
                            reminder["sent_at"] = now.isoformat()
                            changed = True
                            print(
                                f'[TV Guide] Erinnerung gesendet: {reminder["channel"]} – {reminder["title"]}',
                                flush=True,
                            )
                        except Exception as exc:
                            print(f"[TV Guide] Erinnerung konnte nicht gesendet werden: {exc}", flush=True)

                    kept.append(reminder)

                if changed:
                    save_reminders(kept)
        except Exception as exc:
            print(f"[TV Guide] Reminder-Worker Fehler: {exc}", flush=True)

        time.sleep(20)

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
        self.last_refresh_attempt = 0
        self.active_source_url = None
        self._load_parsed_cache()

    def _load_parsed_cache(self):
        try:
            payload = json.loads(PARSED_CACHE_FILE.read_text(encoding="utf-8"))
            source_url = str(payload.get("source_url") or "").strip()
            if source_url not in self._candidate_urls():
                return False

            latest_end_raw = payload.get("feed_latest_end")
            latest_end = datetime.fromisoformat(latest_end_raw) if latest_end_raw else None
            now = datetime.now().astimezone()
            if latest_end and latest_end < now - timedelta(hours=2):
                return False

            cached_by_id = {
                item.get("id"): item
                for item in payload.get("channels", [])
                if isinstance(item, dict) and item.get("id")
            }

            restored = []
            for ch in sorted(CHANNELS["channels"], key=lambda x: x["order"]):
                cached = cached_by_id.get(ch["id"], {})
                restored.append({
                    **ch,
                    "available": bool(cached.get("available")),
                    "programs": cached.get("programs") or [],
                    "source_name": cached.get("source_name"),
                    "source_id": cached.get("source_id"),
                    "logo": cached.get("logo"),
                })

            if not any(item.get("programs") for item in restored):
                return False

            self.channels = restored
            self.last_loaded = payload.get("last_loaded") or payload.get("saved_at")
            self.feed_latest_end = latest_end_raw
            self.active_source_url = source_url
            print(
                "[TV Guide] Persistenter EPG-Cache sofort geladen: "
                f"{sum(1 for item in restored if item.get('available'))} von {len(restored)} Sendern",
                flush=True,
            )
            return True
        except Exception as exc:
            if PARSED_CACHE_FILE.exists():
                print(f"[TV Guide] Persistenter EPG-Cache unbrauchbar: {exc}", flush=True)
            return False

    def _save_parsed_cache(self, source_url):
        try:
            payload = {
                "saved_at": datetime.now().astimezone().isoformat(),
                "last_loaded": self.last_loaded,
                "source_url": source_url,
                "feed_latest_end": self.feed_latest_end,
                "channels": self.channels,
            }
            tmp = PARSED_CACHE_FILE.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
            os.replace(tmp, PARSED_CACHE_FILE)
        except Exception as exc:
            print(f"[TV Guide] Persistenter EPG-Cache konnte nicht gespeichert werden: {exc}", flush=True)

    def _load_state(self):
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _candidate_urls(self):
        urls = [self.options["epg_url"], *FREE_FALLBACK_EPG_URLS]
        out = []
        for url in urls:
            if url and url not in out:
                out.append(url)
        return out

    def _save_state(self, source_url):
        payload = {
            "source_url": source_url,
            "downloaded_at": datetime.now().astimezone().isoformat(),
        }
        STATE_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _cache_fresh(self):
        if not CACHE_FILE.exists():
            return False

        state = self._load_state()
        cached_source = str(state.get("source_url") or "").strip()
        candidates = self._candidate_urls()

        if cached_source not in candidates:
            print(
                "[TV Guide] EPG-Quelle geändert: Cache wird verworfen "
                f"({cached_source or 'unbekannt'} -> {self.options['epg_url']})",
                flush=True,
            )
            return False

        self.active_source_url = cached_source

        age = time.time() - CACHE_FILE.stat().st_mtime
        return age < self.options["refresh_minutes"] * 60

    def _download(self, url):
        req = Request(url, headers={
            "User-Agent": "HomeAssistant-TV-Guide/1.0",
            "Accept-Encoding": "gzip",
        })
        download_tmp = CACHE_FILE.with_suffix(".download")
        cache_tmp = CACHE_FILE.with_suffix(".tmp")
        max_bytes = 100 * 1024 * 1024
        total = 0

        try:
            with urlopen(req, timeout=45) as response, download_tmp.open("wb") as target:
                while True:
                    chunk = response.read(256 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_bytes:
                        raise ValueError("EPG-Datei ist größer als 100 MB.")
                    target.write(chunk)

            with download_tmp.open("rb") as source:
                is_gzip = source.read(2) == b"\x1f\x8b"

            if is_gzip:
                os.replace(download_tmp, cache_tmp)
            else:
                with download_tmp.open("rb") as source, gzip.open(cache_tmp, "wb") as target:
                    while True:
                        chunk = source.read(256 * 1024)
                        if not chunk:
                            break
                        target.write(chunk)
                download_tmp.unlink(missing_ok=True)

            os.replace(cache_tmp, CACHE_FILE)
        finally:
            download_tmp.unlink(missing_ok=True)
            cache_tmp.unlink(missing_ok=True)

        self.source_updated = datetime.now().astimezone().isoformat()
        self.active_source_url = url
        self._save_state(url)
        print(f"[TV Guide] Neuer EPG-Feed geladen: {url}", flush=True)

    def _open_xml(self):
        with CACHE_FILE.open("rb") as source:
            is_gzip = source.read(2) == b"\x1f\x8b"
        return gzip.open(CACHE_FILE, "rb") if is_gzip else CACHE_FILE.open("rb")

    def _build_channel_map(self):
        exact_ids = {}
        exact_names = {}
        shared_source_ids = {}

        for ch in CHANNELS["channels"]:
            internal_id = ch["id"]

            for value in ch.get("xmltv_ids", []):
                key = normalize(value)
                if key:
                    exact_ids.setdefault(key, []).append(internal_id)

            for value in [ch["name"], ch["id"], *ch.get("aliases", [])]:
                key = normalize(value)
                if key:
                    exact_names.setdefault(key, []).append(internal_id)

            for source_id in ch.get("shared_xmltv_ids", []):
                shared_source_ids.setdefault(source_id, []).append(internal_id)

        channel_meta = {}
        claimed_source_ids = set()

        with self._open_xml() as fh:
            for event, elem in ET.iterparse(fh, events=("end",)):
                if elem.tag != "channel":
                    continue

                cid = elem.attrib.get("id", "")
                names = [(x.text or "").strip() for x in elem.findall("display-name") if x.text]
                icon = elem.find("icon")
                icon_url = icon.attrib.get("src") if icon is not None else None

                if cid in shared_source_ids:
                    for internal_id in shared_source_ids[cid]:
                        channel_meta[internal_id] = {
                            "xmltv_id": cid,
                            "display_name": names[0] if names else cid,
                            "icon": icon_url,
                        }
                    elem.clear()
                    continue

                cid_key = normalize(cid)
                name_keys = [normalize(name) for name in names if normalize(name)]

                candidates = []

                # 1) Strongest match: exact XMLTV channel id.
                if cid_key in exact_ids:
                    candidates.extend(exact_ids[cid_key])

                # 2) Exact display-name / configured alias.
                if not candidates:
                    for key in name_keys:
                        candidates.extend(exact_names.get(key, []))

                # 3) Conservative fallback only when the normalized token is long
                #    and the match is unique. This deliberately avoids short-brand
                #    collisions such as RTL / RTLup / RTLZWEI.
                if not candidates:
                    source_keys = [cid_key, *name_keys]
                    fuzzy = set()
                    for skey in source_keys:
                        if len(skey) < 7:
                            continue
                        for known_key, internal_ids in exact_names.items():
                            if len(known_key) < 7:
                                continue
                            if skey.startswith(known_key) or known_key.startswith(skey):
                                fuzzy.update(internal_ids)
                    if len(fuzzy) == 1:
                        candidates = list(fuzzy)

                # Never guess when more than one internal channel matches.
                unique = list(dict.fromkeys(candidates))
                if len(unique) == 1:
                    internal_id = unique[0]
                    if internal_id not in channel_meta and cid not in claimed_source_ids:
                        channel_meta[internal_id] = {
                            "xmltv_id": cid,
                            "display_name": names[0] if names else cid,
                            "icon": icon_url,
                        }
                        claimed_source_ids.add(cid)

                elem.clear()

        return channel_meta

    def _parse(self):
        channel_meta = self._build_channel_map()
        xml_to_internal = {}
        for internal_id, meta in channel_meta.items():
            xml_to_internal.setdefault(meta["xmltv_id"], []).append(internal_id)
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
                internal_ids = xml_to_internal.get(source_id, [])
                if not internal_ids:
                    elem.clear()
                    continue

                start = xmltv_datetime(elem.attrib.get("start"))
                end = xmltv_datetime(elem.attrib.get("stop"))
                if not start or not end:
                    elem.clear()
                    continue

                first_start = start if first_start is None or start < first_start else first_start
                last_start = start if last_start is None or start > last_start else last_start
                latest_end = end if latest_end is None or end > latest_end else latest_end

                icon = elem.find("icon")
                item = {
                    "title": first_text(elem, "title") or "Ohne Titel",
                    "subtitle": first_text(elem, "sub-title"),
                    "desc": first_text(elem, "desc"),
                    "category": first_text(elem, "category"),
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "icon": icon.attrib.get("src") if icon is not None else None,
                }
                for internal_id in internal_ids:
                    programmes[internal_id].append(dict(item))
                    matched_programmes += 1
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

        missing = [ch["name"] for ch in CHANNELS["channels"] if ch["id"] not in channel_meta]
        if missing:
            print("[TV Guide] Nicht im Feed gefunden: " + ", ".join(missing), flush=True)

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

    def _clean_anchor_text(self, fragment):
        text = re.sub(r"<[^>]+>", " ", fragment)
        text = html.unescape(text)
        return re.sub(r"\s+", " ", text).strip()

    def _fetch_radio_bremen_programs(self):
        today = datetime.now().astimezone().date()
        raw_items = []

        for day_index in range(3):
            schedule_date = today + timedelta(days=day_index)
            url = ARD_RB_PROGRAM_URL.format(date=schedule_date.isoformat())
            req = Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 HomeAssistant-TV-Guide/0.3.0",
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
            with urlopen(req, timeout=20) as response:
                page = response.read(8 * 1024 * 1024 + 1)
                if len(page) > 8 * 1024 * 1024:
                    raise ValueError("ARD-Mediathek-Programmseite ist unerwartet groß.")
                charset = response.headers.get_content_charset() or "utf-8"
                page = page.decode(charset, errors="replace")

            anchors = re.findall(r"<a\b[^>]*>(.*?)</a>", page, flags=re.I | re.S)
            day_offset = 0
            previous_minutes = None

            for anchor in anchors:
                text = self._clean_anchor_text(anchor)
                match = re.search(
                    r"(?:LIVE\s+Seit\s+)?(\d{1,2}):(\d{2})\s+Uhr\s+(.+)",
                    text,
                    flags=re.I,
                )
                if not match:
                    continue

                hour = int(match.group(1))
                minute = int(match.group(2))
                title = match.group(3).strip()
                minutes = hour * 60 + minute

                if previous_minutes is not None and minutes + 360 < previous_minutes:
                    day_offset += 1
                previous_minutes = minutes

                start_dt = datetime.combine(
                    schedule_date + timedelta(days=day_offset),
                    datetime.min.time(),
                ).astimezone().replace(hour=hour, minute=minute, second=0, microsecond=0)

                # Remove the live-progress suffix but keep accessibility markers as part of
                # the title only when they are embedded in the official page text.
                title = re.sub(r"\s+\d{1,3}\s*%\s*$", "", title).strip()
                raw_items.append({
                    "title": title or "Ohne Titel",
                    "subtitle": "",
                    "desc": "",
                    "category": "",
                    "start_dt": start_dt,
                    "icon": None,
                })

        unique = {}
        for item in raw_items:
            key = (item["start_dt"].isoformat(), item["title"])
            unique[key] = item

        ordered = sorted(unique.values(), key=lambda x: x["start_dt"])
        programmes = []
        for index, item in enumerate(ordered):
            start_dt = item["start_dt"]
            if index + 1 < len(ordered):
                end_dt = ordered[index + 1]["start_dt"]
            else:
                end_dt = start_dt + timedelta(hours=1)

            if end_dt <= start_dt or end_dt - start_dt > timedelta(hours=6):
                end_dt = start_dt + timedelta(hours=1)

            programmes.append({
                "title": item["title"],
                "subtitle": item["subtitle"],
                "desc": item["desc"],
                "category": item["category"],
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "icon": item["icon"],
            })

        return programmes

    def _supplement_missing_channels(self, channels):
        by_id = {channel["id"]: channel for channel in channels}
        channel = by_id.get("radiobremen")
        if not channel or channel.get("available"):
            return channels

        try:
            programmes = self._fetch_radio_bremen_programs()
            now = datetime.now().astimezone()
            future = [
                item for item in programmes
                if datetime.fromisoformat(item["end"]) >= now - timedelta(hours=6)
            ]
            if not future:
                print(
                    "[TV Guide] ARD-Mediathek-Ergänzung ohne aktuelle Daten: Radio Bremen TV",
                    flush=True,
                )
                return channels

            channel["programs"] = programmes
            channel["available"] = True
            channel["source_name"] = "ARD Mediathek – Radio Bremen"
            channel["source_id"] = "radiobremen/programm"
            print(
                f"[TV Guide] ARD Mediathek ergänzt: Radio Bremen TV mit {len(programmes)} Sendungen",
                flush=True,
            )
        except Exception as exc:
            print(
                f"[TV Guide] ARD-Mediathek-Ergänzung fehlgeschlagen für Radio Bremen TV: {exc}",
                flush=True,
            )

        return channels

    def refresh(self, force=False):
        with self.lock:
            self.refresh_running = True
            self.last_refresh_attempt = time.time()
            self.options = load_options()
            errors = []

            try:
                cache_fresh = self._cache_fresh()
                if not force and cache_fresh:
                    try:
                        self.channels = self._supplement_missing_channels(self._parse())
                        self.last_loaded = datetime.now().astimezone().isoformat()
                        self.last_error = None
                        self._save_parsed_cache(self.active_source_url or self.options["epg_url"])
                        available = sum(1 for ch in self.channels if ch.get("available"))
                        print(
                            f"[TV Guide] EPG geladen: {available} von {len(self.channels)} Sendern "
                            f"mit Programmdaten ({self.active_source_url})",
                            flush=True,
                        )
                        return
                    except Exception as exc:
                        errors.append(f"Cache: {exc}")
                        print(f"[TV Guide] Cache unbrauchbar: {exc}", flush=True)

                for index, url in enumerate(self._candidate_urls(), start=1):
                    try:
                        print(
                            f"[TV Guide] Prüfe EPG-Quelle {index}/{len(self._candidate_urls())}: {url}",
                            flush=True,
                        )
                        self._download(url)
                        self.channels = self._supplement_missing_channels(self._parse())
                        self.last_loaded = datetime.now().astimezone().isoformat()
                        self.last_error = None
                        self._save_parsed_cache(url)
                        available = sum(1 for ch in self.channels if ch.get("available"))
                        print(
                            f"[TV Guide] EPG geladen: {available} von {len(self.channels)} Sendern "
                            f"mit Programmdaten ({url})",
                            flush=True,
                        )
                        return
                    except Exception as exc:
                        errors.append(f"{url}: {exc}")
                        print(f"[TV Guide] EPG-Quelle verworfen: {url} -> {exc}", flush=True)

                self.last_error = " | ".join(errors) if errors else "Keine EPG-Quelle verfügbar."
                print(f"[TV Guide] EPG-Fehler: {self.last_error}", flush=True)
            finally:
                self.refresh_running = False

    def ensure_fresh_async(self):
        retry_due = (time.time() - self.last_refresh_attempt) >= 300
        if not self._cache_fresh() and not self.refresh_running and retry_due:
            self.refresh_running = True
            threading.Thread(target=self.refresh, daemon=True).start()

    def payload(self):
        self.ensure_fresh_async()
        ui = load_options_ui()
        channels = ordered_visible_channels(self.channels)
        if ui.get("max_channels", 0) > 0:
            channels = channels[:ui["max_channels"]]
        return {
            "generated_at": datetime.now().astimezone().isoformat(),
            "profile": CHANNELS["profile"],
            "group": CHANNELS["group"],
            "provider": "XMLTV",
            "source_url": self.active_source_url or self.options["epg_url"],
            "configured_source_url": self.options["epg_url"],
            "fallback_sources": FREE_FALLBACK_EPG_URLS,
            "refresh_minutes": self.options["refresh_minutes"],
            "ui": {
                "default_view": ui.get("default_view", "now"),
                "columns_desktop": ui.get("columns_desktop", 5),
                "max_channels": ui.get("max_channels", 0),
                "theme_mode": ui.get("theme_mode", "auto"),
            },
            "last_loaded": self.last_loaded,
            "feed_latest_end": self.feed_latest_end,
            "error": self.last_error,
            "refresh_running": self.refresh_running,
            "persistent_cache": PARSED_CACHE_FILE.exists(),
            "channel_preferences": load_channel_preferences(),
            "channels": channels,
        }

STORE = EPGStore()

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        raw = urlparse(path).path
        rel = raw.lstrip("/") or "index.html"
        candidate = (WWW / rel).resolve()
        root = WWW.resolve()
        if candidate == root or root in candidate.parents:
            return str(candidate)
        return str(root / "__invalid_path__")

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
        if path.endswith("/api/channel-settings") or path == "/api/channel-settings":
            prefs = load_channel_preferences()
            channel_info = [
                {
                    "id": ch["id"],
                    "name": ch["name"],
                    "logo_file": ch.get("logo_file"),
                    "base_order": ch["order"],
                }
                for ch in sorted(CHANNELS["channels"], key=lambda x: x["order"])
            ]
            return self._json({
                **prefs,
                "channels": channel_info,
            })
        if path.endswith("/api/settings") or path == "/api/settings":
            ui = load_options_ui()
            options = load_options()
            return self._json({
                "default_view": ui["default_view"],
                "columns_desktop": ui["columns_desktop"],
                "max_channels": ui["max_channels"],
                "theme_mode": ui["theme_mode"],
                "epg_url": options["epg_url"],
                "refresh_minutes": options["refresh_minutes"],
                "notification_service": options["notification_service"],
            })
        if path.endswith("/api/notification-services") or path == "/api/notification-services":
            return self._json({"services": list_notification_services()})
        if path.endswith("/api/reminders") or path == "/api/reminders":
            with REMINDER_LOCK:
                return self._json({"reminders": load_reminders()})
        if path.endswith("/api/bookmarks") or path == "/api/bookmarks":
            with BOOKMARK_LOCK:
                stored_bookmarks = load_bookmarks()
                bookmarks = clean_bookmarks(stored_bookmarks)
                if bookmarks != stored_bookmarks:
                    save_bookmarks(bookmarks)
                return self._json({"bookmarks": bookmarks})
        if path.endswith("/api/status") or path == "/api/status":
            return self._json({
                "provider": "XMLTV",
                "source_url": STORE.active_source_url or STORE.options["epg_url"],
                "configured_source_url": STORE.options["epg_url"],
                "fallback_sources": FREE_FALLBACK_EPG_URLS,
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

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        try:
            length = int(self.headers.get("Content-Length") or "0")
            if length <= 0 or length > 65536:
                return self._json({"ok": False, "error": "Ungültige Anfrage."}, status=400)
            payload = json.loads(self.rfile.read(length).decode("utf-8"))

            if path.endswith("/api/channel-settings") or path == "/api/channel-settings":
                if payload.get("reset"):
                    prefs = reset_channel_preferences()
                else:
                    order = payload.get("order")
                    hidden = payload.get("hidden")
                    if not isinstance(order, list) or not isinstance(hidden, list):
                        return self._json({"ok": False, "error": "Ungültige Senderkonfiguration."}, status=400)
                    if not all(isinstance(x, str) for x in order + hidden):
                        return self._json({"ok": False, "error": "Ungültige Sender-IDs."}, status=400)
                    prefs = save_channel_preferences(order, hidden)
                return self._json({"ok": True, **prefs})

            if path.endswith("/api/settings") or path == "/api/settings":
                current_raw = {}
                try:
                    current_raw = json.loads(OPTIONS_FILE.read_text(encoding="utf-8"))
                except Exception:
                    current_raw = {}

                default_view = str(payload.get("default_view") or "now")
                if default_view not in {"now", "2015", "2200"}:
                    return self._json({"ok": False, "error": "Ungültige Standardansicht."}, status=400)

                try:
                    columns = int(payload.get("columns_desktop"))
                    max_channels = int(payload.get("max_channels"))
                    refresh_minutes = int(payload.get("refresh_minutes"))
                except Exception:
                    return self._json({"ok": False, "error": "Ungültige Zahlenwerte."}, status=400)

                if columns < 3 or columns > 6:
                    return self._json({"ok": False, "error": "Sender pro Reihe muss zwischen 3 und 6 liegen."}, status=400)
                if max_channels < 0 or max_channels > 38:
                    return self._json({"ok": False, "error": "Angezeigte Sender muss zwischen 0 und 38 liegen."}, status=400)
                if refresh_minutes < 30 or refresh_minutes > 1440:
                    return self._json({"ok": False, "error": "EPG-Aktualisierung muss zwischen 30 und 1440 Minuten liegen."}, status=400)

                theme_mode = str(payload.get("theme_mode") or "auto").lower()
                if theme_mode not in {"auto", "dark", "light"}:
                    return self._json({"ok": False, "error": "Ungültige Darstellung."}, status=400)

                epg_url = str(payload.get("epg_url") or "").strip()
                if not epg_url.startswith(("http://", "https://")):
                    return self._json({"ok": False, "error": "EPG-Quelle muss eine gültige HTTP- oder HTTPS-Adresse sein."}, status=400)

                notification_service = str(payload.get("notification_service") or "").strip().lower()
                if not re.match(r"^[a-z0-9_]+\.[a-z0-9_]+$", notification_service):
                    return self._json({"ok": False, "error": "Ungültiger Benachrichtigungsdienst."}, status=400)

                try:
                    current_refresh_minutes = int(
                        current_raw.get("refresh_minutes") or DEFAULT_REFRESH_MINUTES
                    )
                except Exception:
                    current_refresh_minutes = DEFAULT_REFRESH_MINUTES

                refresh_needed = (
                    epg_url != str(current_raw.get("epg_url") or DEFAULT_EPG_URL).strip()
                    or refresh_minutes != current_refresh_minutes
                )

                new_options = {
                    "default_view": default_view,
                    "columns_desktop": columns,
                    "max_channels": max_channels,
                    "theme_mode": theme_mode,
                    "epg_url": epg_url,
                    "refresh_minutes": refresh_minutes,
                    "notification_service": notification_service,
                }
                update_addon_options(new_options)

                STORE.options = {
                    "epg_url": epg_url,
                    "refresh_minutes": refresh_minutes,
                    "notification_service": notification_service,
                }
                if refresh_needed and not STORE.refresh_running:
                    threading.Thread(target=STORE.refresh, kwargs={"force": True}, daemon=True).start()

                return self._json({
                    "ok": True,
                    "refresh_started": bool(refresh_needed),
                })

            if path.endswith("/api/reminders") or path == "/api/reminders":
                action = str(payload.get("action") or "")
                reminder_id = str(payload.get("id") or "").strip()
                if not reminder_id:
                    return self._json({"ok": False, "error": "Erinnerungs-ID fehlt."}, status=400)

                with REMINDER_LOCK:
                    reminders = load_reminders()
                    reminders = [item for item in reminders if item.get("id") != reminder_id]

                    if action == "upsert":
                        minutes = int(payload.get("minutes") or 10)
                        if minutes not in {5, 10, 15, 30}:
                            return self._json({"ok": False, "error": "Ungültiger Erinnerungszeitpunkt."}, status=400)

                        start_raw = str(payload.get("start") or "")
                        end_raw = str(payload.get("end") or "")
                        start = datetime.fromisoformat(start_raw).astimezone()
                        end = datetime.fromisoformat(end_raw).astimezone()
                        now = datetime.now().astimezone()
                        if end <= now or start <= now:
                            return self._json({"ok": False, "error": "Für bereits laufende oder beendete Sendungen ist keine Erinnerung möglich."}, status=400)

                        reminders.append({
                            "id": reminder_id,
                            "channel": str(payload.get("channel") or "Unbekannter Sender")[:120],
                            "channelId": str(payload.get("channelId") or "")[:120],
                            "title": str(payload.get("title") or "Sendung")[:240],
                            "start": start.isoformat(),
                            "end": end.isoformat(),
                            "minutes": minutes,
                            "sent": False,
                        })
                    elif action != "remove":
                        return self._json({"ok": False, "error": "Unbekannte Erinnerungsaktion."}, status=400)

                    reminders.sort(key=lambda item: item.get("start", ""))
                    save_reminders(reminders)
                    return self._json({"ok": True, "reminders": reminders})

            if path.endswith("/api/test-notification") or path == "/api/test-notification":
                test = {
                    "id": "tv_guide_test",
                    "channel": "TV Guide",
                    "title": "Testbenachrichtigung",
                    "start": (datetime.now().astimezone() + timedelta(minutes=1)).isoformat(),
                    "end": (datetime.now().astimezone() + timedelta(minutes=2)).isoformat(),
                    "minutes": 1,
                }
                _ha_notification(test)
                return self._json({
                    "ok": True,
                    "service": load_options().get("notification_service", "persistent_notification.create"),
                })

            if path.endswith("/api/bookmarks") or path == "/api/bookmarks":
                action = str(payload.get("action") or "")
                bookmark_id = str(payload.get("id") or "").strip()
                if not bookmark_id:
                    return self._json({"ok": False, "error": "Merklisten-ID fehlt."}, status=400)

                with BOOKMARK_LOCK:
                    bookmarks = clean_bookmarks(load_bookmarks())
                    bookmarks = [item for item in bookmarks if item.get("id") != bookmark_id]

                    if action == "upsert":
                        start_raw = str(payload.get("start") or "")
                        end_raw = str(payload.get("end") or "")
                        start = datetime.fromisoformat(start_raw).astimezone()
                        end = datetime.fromisoformat(end_raw).astimezone()
                        if end <= datetime.now().astimezone():
                            return self._json({"ok": False, "error": "Beendete Sendungen können nicht gemerkt werden."}, status=400)
                        bookmarks.append({
                            "id": bookmark_id,
                            "channel": str(payload.get("channel") or "Unbekannter Sender")[:120],
                            "channelId": str(payload.get("channelId") or "")[:120],
                            "title": str(payload.get("title") or "Sendung")[:240],
                            "start": start.isoformat(),
                            "end": end.isoformat(),
                        })
                    elif action != "remove":
                        return self._json({"ok": False, "error": "Unbekannte Merklistenaktion."}, status=400)

                    bookmarks.sort(key=lambda item: item.get("start", ""))
                    save_bookmarks(bookmarks)

                    if action == "remove":
                        with REMINDER_LOCK:
                            reminders = load_reminders()
                            remaining = [
                                item for item in reminders
                                if item.get("id") != bookmark_id
                            ]
                            if remaining != reminders:
                                save_reminders(remaining)

                    return self._json({"ok": True, "bookmarks": bookmarks})

            return self._json({"ok": False, "error": "Nicht gefunden."}, status=404)
        except Exception as exc:
            return self._json({"ok": False, "error": str(exc)}, status=400)

    def log_message(self, fmt, *args):
        print("[TV Guide]", fmt % args, flush=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8099"))
    print(f"[TV Guide] Webserver startet sofort auf Port {port}", flush=True)
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=STORE.refresh, daemon=True).start()
    threading.Thread(target=reminder_worker, daemon=True).start()
    print("[TV Guide] Ingress ist bereit; EPG wird im Hintergrund geladen", flush=True)
    server.serve_forever()
