import base64
import gzip
import hashlib
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
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent
WWW = BASE / "www"
CHANNELS = json.loads((BASE / "data" / "channels.json").read_text(encoding="utf-8"))
OPTIONS_FILE = Path("/data/options.json")
CACHE_FILE = Path("/data/tv_guide_epg.xml.gz")
PARSED_CACHE_FILE = Path("/data/tv_guide_epg_parsed.json")
CHANNEL_PREFS_FILE = Path("/data/tv_guide_channel_order.json")
REMINDERS_FILE = Path("/data/tv_guide_reminders.json")
BOOKMARKS_FILE = Path("/data/tv_guide_bookmarks.json")
LOGO_CACHE_DIR = Path("/data/tv_guide_logos")
REMINDER_LOCK = threading.Lock()
BOOKMARK_LOCK = threading.Lock()

OPEN_EPG_URL = "https://www.open-epg.com/files/germany.xml.gz"
EPGSHARE_EPG_URL = "https://epgshare01.online/epgshare01/epg_ripper_DE1.xml.gz"
EPGPW_EPG_URL = "https://epg.pw/xmltv/epg_DE.xml.gz"
BUILTIN_EPG_URLS = [OPEN_EPG_URL, EPGSHARE_EPG_URL, EPGPW_EPG_URL]
ARD_RB_PROGRAM_URL = "https://www.ardmediathek.de/radiobremen/programm/{date}"
SWR_PROGRAM_URL = "https://www.swr.de/video/tv-programm/index.html?swx_pcDate={date}&swx_pcStation=7.0.0"
SR_PROGRAM_URL = "https://www.sr.de/sr/epg/tv/srtv/station108~_day-{date}.html"
ARD_PROGRAM_URL = "https://www.ardmediathek.de/programm/{date}"
ZDF_PROGRAM_URL = "https://www.zdf.de/live-tv"

OFFICIAL_PROVIDER_BY_CHANNEL = {
    "ard": {"kind": "ard", "marker": "Das Erste"},
    "zdf": {"kind": "zdf", "marker": "ZDF"},
    "rtl": {"kind": "generic", "url": "https://www.rtl.de/fernsehprogramm/rtl/{date}/"},
    "sat1": {"kind": "generic", "url": "https://www.sat1.de/tv-programm"},
    "prosieben": {"kind": "generic", "url": "https://www.prosieben.de/tv-programm"},
    "kabeleins": {"kind": "generic", "url": "https://www.kabeleins.de/tv-programm"},
    "rtlzwei": {"kind": "generic", "url": "https://www.rtl2.de/tv-programm/{date}"},
    "vox": {"kind": "generic", "url": "https://www.rtl.de/fernsehprogramm/vox/{date}/"},
    "arte": {"kind": "ard", "marker": "arte"},
    "3sat": {"kind": "ard", "marker": "3sat"},
    "ndr": {"kind": "ard", "marker": "NDR"},
    "wdr": {"kind": "ard", "marker": "WDR"},
    "mdr": {"kind": "ard", "marker": "MDR"},
    "rbb": {"kind": "ard", "marker": "RBB"},
    "br": {"kind": "ard", "marker": "BR"},
    "swr": {"kind": "swr"},
    "sr": {"kind": "sr"},
    "hr": {"kind": "ard", "marker": "hr"},
    "radiobremen": {"kind": "radiobremen"},
    "ardalpha": {"kind": "ard", "marker": "ARD alpha"},
    "phoenix": {"kind": "ard", "marker": "phoenix"},
    "tagesschau24": {"kind": "ard", "marker": "tagesschau24"},
    "zdfneo": {"kind": "zdf", "marker": "ZDFneo"},
    "zdfinfo": {"kind": "zdf", "marker": "ZDFinfo"},
    "one": {"kind": "ard", "marker": "ONE"},
    "welt": {"kind": "generic", "url": "https://www.welt.de/tv-programm-live-stream/"},
    "ntv": {"kind": "generic", "url": "https://www.n-tv.de/mediathek/tv/"},
    "disneychannel": {"kind": "generic", "url": "https://tv.disney.de/tv-programm"},
    "n24doku": {"kind": "generic", "url": "https://www.welt.de/tv-programm-n24-doku/"},
    "sixx": {"kind": "generic", "url": "https://www.sixx.de/tv-programm"},
    "prosiebenmaxx": {"kind": "generic", "url": "https://www.prosiebenmaxx.de/tv-programm"},
    "dmax": {"kind": "generic", "url": "https://dmax.de/tv-programm"},
    "sat1gold": {"kind": "generic", "url": "https://www.sat1gold.de/tv-programm"},
    "voxup": {"kind": "generic", "url": "https://www.rtl.de/fernsehprogramm/vox-up/{date}/"},
    "rtlup": {"kind": "generic", "url": "https://www.rtl.de/fernsehprogramm/rtl-up/{date}/"},
    "weltderwunder": {"kind": "generic", "url": "https://www.weltderwunder.de/live-tv/"},
    "df1": {"kind": "generic", "url": "https://df1.de/"},
    "tlc": {"kind": "generic", "url": "https://tlc.de/im-tv"},
    "nitro": {"kind": "generic", "url": "https://www.rtl.de/fernsehprogramm/nitro/{date}/"},
    "tele5": {"kind": "generic", "url": "https://tele5.de/"},
    "superrtl": {"kind": "generic", "url": "https://www.rtl.de/fernsehprogramm/super-rtl/{date}/"},
    "kika": {"kind": "ard", "marker": "KiKA"},
    "eurosport1": {"kind": "generic", "url": "https://www.eurosport.de/watch/schedule.shtml"},
    "sport1": {"kind": "generic", "url": "https://www.sport1.de/tv-video/tv"},
    "esportsone": {"kind": "generic", "url": "https://start.sportdigital.de/tvsender/esportsone"},
    "kabeleinsdoku": {"kind": "generic", "url": "https://www.kabeleinsdoku.de/"},
}

# Every curated main channel goes through the same official-source layer. Channels
# without a stable public schedule endpoint remain XMLTV-only until a verified
# official endpoint is added here; no guessed URLs are used.
OFFICIAL_PROVIDER_AUDIT = {
    channel_id: OFFICIAL_PROVIDER_BY_CHANNEL.get(channel_id)
    for channel_id in [ch["id"] for ch in CHANNELS["channels"]]
}

TELETEXT_PROVIDER_BY_CHANNEL = {
    "ard": {
        "today": [f"https://origin.ard-text.de/mobil/{page}" for page in range(301, 305)],
        "tomorrow": [f"https://origin.ard-text.de/mobil/{page}" for page in range(305, 309)],
    },
    "zdf": {
        "today": [f"https://teletext.zdf.de/teletext/zdf/seiten/{page}.html" for page in range(301, 305)],
        "tomorrow": [f"https://teletext.zdf.de/teletext/zdf/seiten/{page}.html" for page in range(350, 354)],
    },
    "zdfneo": {
        "today": [f"https://teletext.zdf.de/teletext/zdfneo/seiten/{page}.html" for page in range(301, 305)],
        "tomorrow": [f"https://teletext.zdf.de/teletext/zdfneo/seiten/{page}.html" for page in range(350, 354)],
    },
    "zdfinfo": {
        "today": [f"https://teletext.zdf.de/teletext/zdfinfo/seiten/{page}.html" for page in range(301, 305)],
        "tomorrow": [f"https://teletext.zdf.de/teletext/zdfinfo/seiten/{page}.html" for page in range(350, 354)],
    },
    "3sat": {
        "today": [f"https://teletext.zdf.de/teletext/3sat/seiten/{page}.html" for page in range(301, 305)],
        "tomorrow": [f"https://teletext.zdf.de/teletext/3sat/seiten/{page}.html" for page in range(350, 354)],
    },
    "wdr": {
        "today": [f"https://mobiltext.wdr.de/{page}.html" for page in range(301, 305)],
        "tomorrow": [f"https://mobiltext.wdr.de/{page}.html" for page in range(325, 329)],
    },
    "ndr": {
        "today": [f"https://www.ndr.de/public/teletext/{page}_01.htm" for page in range(301, 306)],
        "tomorrow": [f"https://www.ndr.de/public/teletext/{page}_01.htm" for page in range(306, 311)],
    },
}

SECONDARY_WEB_PROVIDER_BY_CHANNEL = {
    "euronews": "https://tvgid.de/channels/de-euron-d?date={date}",
    "hgtv": "https://tvgid.de/channels/de-hgtv?date={date}",
    "nickelodeon": "https://tvgid.de/channels/de-nick?date={date}",
    "comedycentral": "https://tvgid.de/channels/de-comedy-central?date={date}",
}

DEFAULT_REFRESH_MINUTES = 180

def save_options_file(options):
    tmp = OPTIONS_FILE.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(options, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(tmp, OPTIONS_FILE)

def load_options():
    try:
        data = json.loads(OPTIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    try:
        refresh = int(data.get("refresh_minutes") or DEFAULT_REFRESH_MINUTES)
    except Exception:
        refresh = DEFAULT_REFRESH_MINUTES
    notification_service = str(
        data.get("notification_service") or "persistent_notification.create"
    ).strip().lower()
    if not re.match(r"^[a-z0-9_]+\.[a-z0-9_]+$", notification_service):
        notification_service = "persistent_notification.create"
    return {
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
        "max_channels": max(0, min(500, max_channels)),
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

def feed_channel_id(source_id):
    digest = hashlib.sha1(str(source_id or "").encode("utf-8")).hexdigest()[:16]
    return f"epg_{digest}"

def _logo_source_for_channel(channel, theme):
    if theme == "light":
        candidates = [
            channel.get("logo_file_light"),
            channel.get("logo_file"),
            channel.get("logo_light"),
            channel.get("logo"),
            channel.get("logo_url"),
        ]
    else:
        candidates = [
            channel.get("logo_file"),
            channel.get("logo_file_light"),
            channel.get("logo_dark"),
            channel.get("logo"),
            channel.get("logo_url"),
        ]
    return next((str(value).strip() for value in candidates if value), "")


def _logo_mime(source, content_type, data):
    value = (content_type or "").split(";", 1)[0].strip().lower()
    if value in {"image/svg+xml", "image/png", "image/jpeg", "image/webp", "image/gif"}:
        return value
    lower = str(source or "").lower()
    if lower.endswith(".svg") or data.lstrip().startswith(b"<svg"):
        return "image/svg+xml"
    if data.startswith(b"\x89PNG"):
        return "image/png"
    if data.startswith(b"\xff\xd8"):
        return "image/jpeg"
    if data.startswith(b"RIFF") and b"WEBP" in data[:16]:
        return "image/webp"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    return None


def _read_logo_source(source):
    if not source:
        return None
    if source.startswith(("http://", "https://")):
        req = Request(
            source,
            headers={
                "User-Agent": "Mozilla/5.0 HomeAssistant-TV-Guide/1.0",
                "Accept": "image/avif,image/webp,image/svg+xml,image/*,*/*;q=0.8",
            },
        )
        with urlopen(req, timeout=10) as response:
            data = response.read(2 * 1024 * 1024 + 1)
            if len(data) > 2 * 1024 * 1024:
                return None
            mime = _logo_mime(source, response.headers.get("Content-Type"), data)
            return (data, mime) if mime else None

    path = (WWW / source.lstrip("/")).resolve()
    if WWW.resolve() not in path.parents:
        return None
    if not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
        return None
    data = path.read_bytes()
    mime = _logo_mime(source, None, data)
    return (data, mime) if mime else None


def _normalized_logo_svg(data, mime, theme):
    encoded = base64.b64encode(data).decode("ascii")
    image_href = f"data:{mime};base64,{encoded}"
    if theme == "dark":
        filter_def = """
  <filter id="logo-outline" x="-12%" y="-20%" width="124%" height="140%">
    <feMorphology in="SourceAlpha" operator="dilate" radius="1.25" result="dilated"/>
    <feFlood flood-color="#f4f6f8" flood-opacity="0.96" result="outlineColor"/>
    <feComposite in="outlineColor" in2="dilated" operator="in" result="outline"/>
    <feGaussianBlur in="outline" stdDeviation="0.28" result="softOutline"/>
    <feMerge><feMergeNode in="softOutline"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>"""
        image_filter = ' filter="url(#logo-outline)"'
    else:
        filter_def = ""
        image_filter = ""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="260" height="64" viewBox="0 0 260 64">
{filter_def}
  <image x="5" y="4" width="250" height="56" preserveAspectRatio="xMidYMid meet"
         href="{image_href}"{image_filter}/>
</svg>
"""


def _normalized_text_logo_svg(name, theme):
    label = html.escape(str(name or "TV"))
    length = len(str(name or "TV"))
    font_size = 30 if length <= 10 else 24 if length <= 18 else 19
    fill = "#f4f6f8" if theme == "dark" else "#20242a"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="260" height="64" viewBox="0 0 260 64">
  <text x="130" y="39" text-anchor="middle"
        font-family="Arial,Helvetica,sans-serif" font-size="{font_size}"
        font-weight="700" fill="{fill}">{label}</text>
</svg>
"""


def normalized_logo_path(channel, theme):
    theme = "dark" if theme == "dark" else "light"
    source = _logo_source_for_channel(channel, theme)
    source_key_value = source or f"text:{channel.get('name') or channel.get('id') or 'TV'}"
    source_key = hashlib.sha1(source_key_value.encode("utf-8")).hexdigest()[:12]
    channel_key = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(channel.get("id") or "channel"))
    LOGO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    target = LOGO_CACHE_DIR / f"{channel_key}-{theme}-{source_key}.svg"
    if target.is_file() and target.stat().st_size > 100:
        return target

    try:
        tmp = target.with_suffix(".tmp")
        if not source:
            tmp.write_text(
                _normalized_text_logo_svg(channel.get("name"), theme),
                encoding="utf-8",
            )
            os.replace(tmp, target)
            return target

        loaded = _read_logo_source(source)
        if not loaded:
            tmp.write_text(
                _normalized_text_logo_svg(channel.get("name"), theme),
                encoding="utf-8",
            )
            os.replace(tmp, target)
            return target
        data, mime = loaded
        tmp.write_text(_normalized_logo_svg(data, mime, theme), encoding="utf-8")
        os.replace(tmp, target)
        return target
    except Exception as exc:
        print(
            f"[TV Guide] Logo konnte nicht normalisiert werden ({channel.get('name')} / {theme}): {exc}",
            flush=True,
        )
        return None


def normalized_logo_urls(channel):
    channel_id = str(channel.get("id") or "")
    if not channel_id:
        return (None, None)
    encoded_id = quote(channel_id, safe="")
    base = f"api/channel-logo/{encoded_id}"
    return (f"{base}/light.svg", f"{base}/dark.svg")


def known_channel_ids():
    ids = set(base_channel_ids())
    store = globals().get("STORE")
    if store is not None:
        ids.update(ch.get("id") for ch in getattr(store, "channels", []) if ch.get("id"))
    return ids

def merge_channel_order(saved_order):
    default_order = base_channel_ids()
    known = known_channel_ids()
    order = []

    for channel_id in saved_order or []:
        if channel_id in known and channel_id not in order:
            order.append(channel_id)

    # Keep the curated main channels as the default preset. Newly discovered
    # feed channels stay available in the catalogue but are not enabled
    # automatically.
    for channel_id in default_order:
        if channel_id in order:
            continue
        base_index = default_order.index(channel_id)
        following = next((x for x in default_order[base_index + 1:] if x in order), None)
        if following:
            order.insert(order.index(following), channel_id)
            continue
        preceding = next((x for x in reversed(default_order[:base_index]) if x in order), None)
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
    known = known_channel_ids()
    hidden = [x for x in raw.get("hidden", []) if x in known]
    return {"order": order, "hidden": hidden}

def save_channel_preferences(order, hidden):
    known = known_channel_ids()
    clean_order = []
    for channel_id in order or []:
        if channel_id in known and channel_id not in clean_order:
            clean_order.append(channel_id)

    prefs = {
        "order": clean_order,
        "hidden": [x for x in hidden if x in known],
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
    return [
        by_id[channel_id]
        for channel_id in prefs["order"]
        if channel_id in by_id and channel_id not in hidden
    ]

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
        self.refresh_running = False
        self.feed_latest_end = None
        self.last_refresh_attempt = 0
        self.source_metrics = []
        self.official_metrics = {
            "attempted": 0,
            "enriched": 0,
            "teletext_channels": 0,
            "missing_official": [],
        }
        self._load_parsed_cache()

    def _load_parsed_cache(self):
        try:
            payload = json.loads(PARSED_CACHE_FILE.read_text(encoding="utf-8"))
            latest_end_raw = payload.get("feed_latest_end")
            latest_end = datetime.fromisoformat(latest_end_raw) if latest_end_raw else None
            now = datetime.now().astimezone()
            if latest_end and latest_end < now - timedelta(hours=2):
                return False

            cached_channels = [
                item for item in payload.get("channels", [])
                if isinstance(item, dict) and item.get("id")
            ]
            configured_by_id = {ch["id"]: ch for ch in CHANNELS["channels"]}

            restored = []
            for item in cached_channels:
                channel_id = item["id"]
                if channel_id in configured_by_id:
                    restored.append({
                        **configured_by_id[channel_id],
                        **item,
                        "preset": True,
                        "catalog_group": "Hauptsender",
                    })
                else:
                    restored.append(dict(item))

            # Older caches may not contain every configured main channel yet.
            existing_ids = {item["id"] for item in restored}
            for ch in sorted(CHANNELS["channels"], key=lambda x: x["order"]):
                if ch["id"] in existing_ids:
                    continue
                restored.append({
                    **ch,
                    "preset": True,
                    "catalog_group": "Hauptsender",
                    "available": False,
                    "programs": [],
                    "source_name": None,
                    "source_id": None,
                    "logo": None,
                    "logo_light": ch.get("logo_file_light") or ch.get("logo_file"),
                    "logo_dark": ch.get("logo_file") or ch.get("logo_file_light"),
                })

            if not any(item.get("programs") for item in restored):
                return False

            restored.sort(key=lambda ch: (
                0 if ch.get("preset") else 1,
                ch.get("order", 99999) if ch.get("preset") else 99999,
                str(ch.get("name") or "").casefold(),
            ))

            self.channels = restored
            self.last_loaded = payload.get("last_loaded") or payload.get("saved_at")
            self.feed_latest_end = latest_end_raw
            self.source_metrics = list(payload.get("source_metrics") or [])
            self.official_metrics = dict(payload.get("official_metrics") or self.official_metrics)
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
                "source_metrics": self.source_metrics,
                "official_metrics": self.official_metrics,
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

    def _candidate_urls(self):
        return list(BUILTIN_EPG_URLS)

    def _cache_fresh(self):
        if not PARSED_CACHE_FILE.exists():
            return False
        if not any(channel.get("programs") for channel in self.channels):
            return False
        age = time.time() - PARSED_CACHE_FILE.stat().st_mtime
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

        print(f"[TV Guide] Neuer EPG-Feed geladen: {url}", flush=True)

    def _open_xml(self):
        with CACHE_FILE.open("rb") as source:
            is_gzip = source.read(2) == b"\x1f\x8b"
        return gzip.open(CACHE_FILE, "rb") if is_gzip else CACHE_FILE.open("rb")

    def _build_channel_map(self):
        exact_ids = {}
        exact_names = {}
        shared_source_ids = {}
        configured_by_id = {ch["id"]: ch for ch in CHANNELS["channels"]}

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
                display_name = names[0] if names else cid

                if cid in shared_source_ids:
                    for internal_id in shared_source_ids[cid]:
                        channel_meta[internal_id] = {
                            "xmltv_id": cid,
                            "display_name": display_name,
                            "icon": icon_url,
                            "configured": True,
                        }
                    claimed_source_ids.add(cid)
                    elem.clear()
                    continue

                cid_key = normalize(cid)
                name_keys = [normalize(name) for name in names if normalize(name)]
                candidates = []

                if cid_key in exact_ids:
                    candidates.extend(exact_ids[cid_key])

                if not candidates:
                    for key in name_keys:
                        candidates.extend(exact_names.get(key, []))

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

                unique = list(dict.fromkeys(candidates))
                if len(unique) == 1 and cid not in claimed_source_ids:
                    internal_id = unique[0]
                    if internal_id not in channel_meta:
                        channel_meta[internal_id] = {
                            "xmltv_id": cid,
                            "display_name": display_name,
                            "icon": icon_url,
                            "configured": True,
                        }
                        claimed_source_ids.add(cid)
                        elem.clear()
                        continue

                # Every unmatched XMLTV channel is still part of the catalogue.
                # The source id is hashed only for the stable internal key; the
                # original XMLTV id remains available as source_id.
                dynamic_id = feed_channel_id(cid)
                suffix = 1
                while dynamic_id in channel_meta or dynamic_id in configured_by_id:
                    dynamic_id = f"{feed_channel_id(cid)}_{suffix}"
                    suffix += 1

                channel_meta[dynamic_id] = {
                    "xmltv_id": cid,
                    "display_name": display_name,
                    "icon": icon_url,
                    "configured": False,
                }
                claimed_source_ids.add(cid)
                elem.clear()

        return channel_meta

    def _parse(self):
        channel_meta = self._build_channel_map()
        configured_by_id = {ch["id"]: ch for ch in CHANNELS["channels"]}

        xml_to_internal = {}
        for internal_id, meta in channel_meta.items():
            xml_to_internal.setdefault(meta["xmltv_id"], []).append(internal_id)

        programmes = {internal_id: [] for internal_id in channel_meta}
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
            f"{len(channel_meta)} Sender im Feed-Katalog, "
            f"{seen_programmes} Programme im Feed, "
            f"{matched_programmes} Programme übernommen"
            + (f", Zeitraum {first_start.isoformat()} bis {last_start.isoformat()}" if first_start and last_start else ""),
            flush=True,
        )

        result = []
        dynamic_order = 10000
        for internal_id, meta in channel_meta.items():
            items = sorted(programmes.get(internal_id, []), key=lambda x: x["start"])
            configured = configured_by_id.get(internal_id)

            if configured:
                channel = {
                    **configured,
                    "preset": True,
                    "catalog_group": "Hauptsender",
                    "logo": meta.get("icon"),
                    "logo_light": configured.get("logo_file_light") or configured.get("logo_file"),
                    "logo_dark": configured.get("logo_file") or configured.get("logo_file_light"),
                }
            else:
                channel = {
                    "order": dynamic_order,
                    "id": internal_id,
                    "name": meta.get("display_name") or meta.get("xmltv_id") or internal_id,
                    "aliases": [],
                    "xmltv_ids": [meta.get("xmltv_id")],
                    "logo_file": None,
                    "logo_file_light": None,
                    "preset": False,
                    "catalog_group": "Weitere Sender",
                    "logo": meta.get("icon"),
                    # Most XMLTV providers expose one official logo. Keep
                    # separate theme fields so providers with two variants can
                    # be supported without changing the catalogue model.
                    "logo_light": meta.get("icon"),
                    "logo_dark": meta.get("icon"),
                }
                dynamic_order += 1

            channel.update({
                "source_name": meta.get("display_name"),
                "source_id": meta.get("xmltv_id"),
                "available": bool(items),
                "programs": items,
            })
            result.append(channel)

        # Keep the complete configured main-channel set stable even when the
        # current XMLTV feed temporarily omits one or more stations.
        existing_ids = {item["id"] for item in result}
        for configured in sorted(CHANNELS["channels"], key=lambda x: x["order"]):
            if configured["id"] in existing_ids:
                continue
            result.append({
                **configured,
                "preset": True,
                "catalog_group": "Hauptsender",
                "logo": configured.get("logo_url"),
                "logo_light": configured.get("logo_file_light") or configured.get("logo_file") or configured.get("logo_url"),
                "logo_dark": configured.get("logo_file") or configured.get("logo_file_light") or configured.get("logo_url"),
                "source_name": None,
                "source_id": None,
                "available": False,
                "programs": [],
            })

        result.sort(key=lambda ch: (
            0 if ch.get("preset") else 1,
            ch.get("order", 99999) if ch.get("preset") else 99999,
            str(ch.get("name") or "").casefold(),
        ))
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

    def _fetch_html(self, url, label):
        cache = getattr(self, "_official_html_cache", None)
        if isinstance(cache, dict) and url in cache:
            return cache[url]

        req = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 HomeAssistant-TV-Guide/1.0",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with urlopen(req, timeout=20) as response:
            page = response.read(8 * 1024 * 1024 + 1)
            if len(page) > 8 * 1024 * 1024:
                raise ValueError(f"{label}-Programmseite ist unerwartet groß.")
            charset = response.headers.get_content_charset() or "utf-8"
            page = page.decode(charset, errors="replace")

        if isinstance(cache, dict):
            cache[url] = page
        return page

    def _build_programmes_from_starts(self, raw_items):
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
                "subtitle": item.get("subtitle", ""),
                "desc": item.get("desc", ""),
                "category": item.get("category", ""),
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "icon": item.get("icon"),
            })
        return programmes

    def _html_lines(self, page):
        page = re.sub(r"<!--.*?-->", " ", page, flags=re.S)
        page = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", page, flags=re.I | re.S)
        page = re.sub(
            r"</?(?:h[1-6]|p|div|li|article|section|br|tr|td|th|option|button)\b[^>]*>",
            "\n",
            page,
            flags=re.I,
        )
        page = html.unescape(re.sub(r"<[^>]+>", " ", page))
        lines = []
        for raw in page.splitlines():
            line = re.sub(r"\s+", " ", raw).strip()
            if line:
                lines.append(line)
        return lines

    def _schedule_title_candidate(self, lines, index):
        ignored = {
            "heute", "morgen", "übermorgen", "gestern", "jetzt",
            "nachts", "morgens", "vormittag", "mittags", "nachmittags",
            "abends", "live", "tv-programm", "programm", "mehr erfahren",
        }
        for offset in (1, -1, 2):
            candidate_index = index + offset
            if candidate_index < 0 or candidate_index >= len(lines):
                continue
            candidate = lines[candidate_index].strip()
            normalized = normalize(candidate)
            if not candidate or normalized in {normalize(x) for x in ignored}:
                continue
            if re.match(r"^\d{1,2}[:.]\d{2}(?:\s*[-–]\s*\d{1,2}[:.]\d{2})?$", candidate):
                continue
            if len(candidate) > 240:
                continue
            return candidate
        return ""

    def _parse_schedule_lines(self, lines, schedule_date, max_programmes=100):
        raw_items = []
        previous_minutes = None
        day_offset = 0
        skip_indices = set()

        for index, line in enumerate(lines):
            if index in skip_indices:
                continue

            match = re.match(
                r"^(\d{1,2})[:.](\d{2})(?:\s*[-–]\s*\d{1,2}[:.]\d{2})?\s*(.*)$",
                line,
            )
            if not match:
                continue

            hour = int(match.group(1))
            minute = int(match.group(2))
            if hour > 23 or minute > 59:
                continue

            title = match.group(3).strip(" -–")

            # Some public programme pages render start time, end time and title
            # as three consecutive text lines. Treat the second time as the end
            # marker instead of a second programme.
            if not title and index + 2 < len(lines):
                next_time = re.match(r"^(\d{1,2})[:.](\d{2})$", lines[index + 1])
                following = lines[index + 2].strip()
                if next_time and following and not re.match(
                    r"^\d{1,2}[:.]\d{2}", following
                ):
                    title = following
                    skip_indices.add(index + 1)

            if not title:
                title = self._schedule_title_candidate(lines, index)
            if not title:
                continue

            minutes = hour * 60 + minute
            if previous_minutes is not None and minutes + 360 < previous_minutes:
                day_offset += 1
            previous_minutes = minutes

            start_dt = datetime.combine(
                schedule_date + timedelta(days=day_offset),
                datetime.min.time(),
            ).astimezone().replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0,
            )
            raw_items.append({
                "title": title,
                "subtitle": "",
                "desc": "",
                "category": "",
                "start_dt": start_dt,
                "icon": None,
            })
            if len(raw_items) >= max_programmes:
                break

        return self._build_programmes_from_starts(raw_items)

    def _provider_section(self, lines, channel_id, provider):
        kind = provider.get("kind")
        marker = str(provider.get("marker") or "").strip()
        if kind not in {"ard", "zdf"} or not marker:
            return lines

        family_markers = [
            str(item.get("marker") or "").strip()
            for item in OFFICIAL_PROVIDER_BY_CHANNEL.values()
            if item and item.get("kind") == kind and item.get("marker")
        ]

        start = None
        marker_key = normalize(marker)
        for index, line in enumerate(lines):
            line_key = normalize(line)
            if line_key == marker_key or line_key.startswith(marker_key):
                start = index + 1
                break

        if start is None and channel_id == "ard" and kind == "ard":
            start = next(
                (
                    index + 1
                    for index, line in enumerate(lines)
                    if normalize(line) == normalize("Programmübersicht")
                ),
                0,
            )

        if start is None:
            return []

        end = len(lines)
        other_keys = {
            normalize(value)
            for value in family_markers
            if normalize(value) != marker_key
        }
        for index in range(start, len(lines)):
            line_key = normalize(lines[index])
            if any(line_key == key or line_key.startswith(key) for key in other_keys):
                end = index
                break
        return lines[start:end]

    def _fetch_generic_official_programs(self, channel_id, provider):
        today = datetime.now().astimezone().date()
        url_template = provider.get("url")
        kind = provider.get("kind")

        if kind == "ard":
            url_template = ARD_PROGRAM_URL
        elif kind == "zdf":
            url_template = ZDF_PROGRAM_URL

        if not url_template:
            return []

        programmes = []
        day_count = 3 if "{date}" in url_template else 1
        for day_index in range(day_count):
            schedule_date = today + timedelta(days=day_index)
            url = url_template.format(date=schedule_date.isoformat())
            page = self._fetch_html(url, channel_id)
            lines = self._html_lines(page)
            lines = self._provider_section(lines, channel_id, provider)
            if not lines:
                continue
            programmes.extend(
                self._parse_schedule_lines(
                    lines,
                    schedule_date,
                    max_programmes=120,
                )
            )

        by_start = {}
        for item in programmes:
            start = item.get("start")
            if start and start not in by_start:
                by_start[start] = item
        return sorted(by_start.values(), key=lambda item: item.get("start") or "")

    def _fetch_teletext_programs(self, channel_id):
        provider = TELETEXT_PROVIDER_BY_CHANNEL.get(channel_id)
        if not provider:
            return []

        today = datetime.now().astimezone().date()
        programmes = []
        for day_key, date_offset in (("today", 0), ("tomorrow", 1)):
            schedule_date = today + timedelta(days=date_offset)
            for url in provider.get(day_key, []):
                try:
                    page = self._fetch_html(url, f"{channel_id} Videotext")
                    lines = self._html_lines(page)
                    programmes.extend(
                        self._parse_schedule_lines(
                            lines,
                            schedule_date,
                            max_programmes=120,
                        )
                    )
                except Exception as exc:
                    print(
                        f"[TV Guide] Videotext-Seite übersprungen für {channel_id}: "
                        f"{url} -> {exc}",
                        flush=True,
                    )

        by_start = {}
        for item in programmes:
            start = item.get("start")
            if not start:
                continue
            current = by_start.get(start)
            if current is None or self._programme_score(item) > self._programme_score(current):
                by_start[start] = item
        return sorted(by_start.values(), key=lambda item: item.get("start") or "")

    def _fetch_secondary_web_programs(self, channel_id):
        url_template = SECONDARY_WEB_PROVIDER_BY_CHANNEL.get(channel_id)
        if not url_template:
            return []

        today = datetime.now().astimezone().date()
        programmes = []
        for day_index in range(3):
            schedule_date = today + timedelta(days=day_index)
            url = url_template.format(date=schedule_date.isoformat())
            page = self._fetch_html(url, f"{channel_id} Sekundärquelle")
            programmes.extend(
                self._parse_schedule_lines(
                    self._html_lines(page),
                    schedule_date,
                    max_programmes=140,
                )
            )
        return self._merge_program_lists([], programmes)

    def _fetch_official_programs(self, channel_id, provider):
        kind = provider.get("kind")
        if kind == "radiobremen":
            return self._fetch_radio_bremen_programs()
        if kind == "swr":
            return self._fetch_swr_programs()
        if kind == "sr":
            return self._fetch_sr_programs()
        return self._fetch_generic_official_programs(channel_id, provider)

    def _fetch_swr_programs(self):
        today = datetime.now().astimezone().date()
        raw_items = []

        for day_index in range(3):
            schedule_date = today + timedelta(days=day_index)
            page = self._fetch_html(
                SWR_PROGRAM_URL.format(date=schedule_date.isoformat()),
                "SWR",
            )
            lines = self._html_lines(page)

            pending_start = None
            for line in lines:
                match = re.match(
                    r"^(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{2})$",
                    line,
                )
                if match:
                    day, month, year, hour, minute = map(int, match.groups())
                    try:
                        date_value = datetime(year, month, day).date()
                    except ValueError:
                        pending_start = None
                        continue
                    pending_start = datetime.combine(
                        date_value,
                        datetime.min.time(),
                    ).astimezone().replace(
                        hour=hour,
                        minute=minute,
                        second=0,
                        microsecond=0,
                    )
                    continue

                if pending_start is None:
                    continue

                title = line.strip()
                if not title:
                    continue
                normalized = normalize(title)
                if normalized in {
                    "untertitel",
                    "wiederholung",
                    "tagestipp",
                    "deutschegebardensprache",
                    "audiodeskription",
                }:
                    continue
                if title.startswith(("Stand", "Erstmals publiziert", "Autor/in")):
                    continue
                if len(title) > 240:
                    continue

                raw_items.append({
                    "title": title,
                    "subtitle": "",
                    "desc": "",
                    "category": "",
                    "start_dt": pending_start,
                    "icon": None,
                })
                pending_start = None

        return self._build_programmes_from_starts(raw_items)

    def _fetch_sr_programs(self):
        today = datetime.now().astimezone().date()
        programmes = []

        for day_index in range(3):
            schedule_date = today + timedelta(days=day_index)
            page = self._fetch_html(
                SR_PROGRAM_URL.format(date=schedule_date.isoformat()),
                "SR",
            )
            lines = self._html_lines(page)

            # SR renders programme items as visible lines such as
            # "20:15 Wildes Italien". Parsing the page text is more robust
            # than depending on the current link/container markup.
            day_programmes = self._parse_schedule_lines(
                lines,
                schedule_date,
                max_programmes=100,
            )
            programmes.extend(day_programmes)

        return self._merge_program_lists([], programmes)

    def _supplement_missing_channels(self, channels):
        by_id = {channel["id"]: channel for channel in channels}
        now = datetime.now().astimezone()
        self._official_html_cache = {}
        enriched = 0
        attempted = 0
        provider_results = {}

        try:
            for channel_id in base_channel_ids():
                channel = by_id.get(channel_id)
                provider = OFFICIAL_PROVIDER_AUDIT.get(channel_id)
                if not channel:
                    provider_results[channel_id] = {
                        "status": "channel_missing",
                        "programmes": 0,
                    }
                    continue
                secondary_url = SECONDARY_WEB_PROVIDER_BY_CHANNEL.get(channel_id)
                if not provider and not secondary_url:
                    provider_results[channel_id] = {
                        "status": "no_verified_provider",
                        "programmes": 0,
                    }
                    continue

                attempted += 1
                try:
                    official = self._fetch_official_programs(channel_id, provider) if provider else []
                    teletext = self._fetch_teletext_programs(channel_id)
                    secondary = self._fetch_secondary_web_programs(channel_id)
                    official = self._merge_program_lists(official, teletext)
                    official = self._merge_program_lists(official, secondary)
                    official = [
                        item for item in official
                        if datetime.fromisoformat(item["end"]) >= now - timedelta(hours=6)
                    ]
                    if not official:
                        provider_results[channel_id] = {
                            "status": "no_data",
                            "programmes": 0,
                            "teletext": bool(teletext),
                            "secondary": bool(secondary),
                        }
                        continue

                    before_count = len(channel.get("programs") or [])
                    merged = self._merge_program_lists(channel.get("programs") or [], official)
                    if not merged:
                        provider_results[channel_id] = {
                            "status": "no_data",
                            "programmes": 0,
                            "teletext": bool(teletext),
                        }
                        continue

                    channel["programs"] = merged
                    channel["available"] = True
                    source_label = (
                        provider.get("url") or provider.get("kind")
                        if provider else "Sekundäre Web-Programmquelle"
                    )
                    if TELETEXT_PROVIDER_BY_CHANNEL.get(channel_id):
                        source_label = f"{source_label} + Videotext"
                    if secondary_url:
                        source_label = f"{source_label} + Sekundärquelle"
                    channel["official_source"] = source_label
                    if before_count == 0:
                        channel["source_name"] = (
                            f"Offizielle Quelle – {channel.get('name')}"
                            if provider
                            else f"Sekundäre Webquelle – {channel.get('name')}"
                        )
                    else:
                        addition = "offizielle Quelle" if provider else "Sekundärquelle"
                        channel["source_name"] = (
                            f"{channel.get('source_name') or 'XMLTV'} + {addition}"
                        )
                    enriched += 1
                    provider_results[channel_id] = {
                        "status": "ok",
                        "programmes": len(official),
                        "merged_programmes": len(merged),
                        "teletext": bool(teletext),
                        "secondary": bool(secondary),
                    }
                except Exception as exc:
                    provider_results[channel_id] = {
                        "status": "error",
                        "programmes": 0,
                        "error": str(exc)[:240],
                    }
                    print(
                        f"[TV Guide] Offizielle Provider-Ergänzung fehlgeschlagen für "
                        f"{channel.get('name')}: {exc}",
                        flush=True,
                    )
        finally:
            self._official_html_cache = {}

        missing_official = [
            channel_id
            for channel_id in base_channel_ids()
            if OFFICIAL_PROVIDER_AUDIT.get(channel_id) is None
        ]
        self.official_metrics = {
            "attempted": attempted,
            "enriched": enriched,
            "teletext_channels": len(TELETEXT_PROVIDER_BY_CHANNEL),
            "secondary_web_channels": len(SECONDARY_WEB_PROVIDER_BY_CHANNEL),
            "missing_official": missing_official,
            "provider_results": provider_results,
        }
        print(
            f"[TV Guide] Provider-Abdeckung: {enriched}/{attempted} Sender ergänzt; "
            f"{len(missing_official)} ohne offiziellen Endpunkt, "
            f"{len(SECONDARY_WEB_PROVIDER_BY_CHANNEL)} davon mit Sekundärquelle",
            flush=True,
        )
        for channel_id in base_channel_ids():
            result = provider_results.get(channel_id, {"status": "unknown"})
            print(
                f"[TV Guide] Provider-Check {channel_id}: "
                f"{result.get('status')} ({result.get('programmes', 0)} Programme)",
                flush=True,
            )
        return channels

    def _validate_feed_quality(self, channels):
        available = sum(1 for channel in channels if channel.get("available"))
        main_available = sum(
            1 for channel in channels
            if channel.get("preset") and channel.get("available")
        )
        programme_count = sum(
            len(channel.get("programs") or [])
            for channel in channels
            if channel.get("available")
        )
        latest_end = (
            datetime.fromisoformat(self.feed_latest_end)
            if self.feed_latest_end else None
        )
        now = datetime.now().astimezone()

        # Partial sources are useful in a merge architecture. Reject only
        # feeds that contain no usable programmes or are already effectively
        # stale. A small source may still fill a gap that larger feeds miss.
        if available < 1 or programme_count < 1:
            raise ValueError("EPG-Quelle enthält keine verwertbaren Programmdaten.")
        if latest_end is None or latest_end < now + timedelta(hours=2):
            raise ValueError(
                "EPG-Quelle enthält keine ausreichend aktuellen Programmdaten."
            )

        coverage = "breit" if available >= 80 and main_available >= 25 else "teilweise"
        print(
            f"[TV Guide] EPG-Qualität akzeptiert ({coverage}): "
            f"{available} Sender mit Programmdaten, {main_available}/50 Hauptsender, "
            f"{programme_count} Programme, Daten bis {latest_end.isoformat()}",
            flush=True,
        )

    def _programme_score(self, item):
        return sum(
            1 for key in ("title", "subtitle", "desc", "category", "icon")
            if str(item.get(key) or "").strip()
        ) + min(len(str(item.get("desc") or "")) // 80, 4)

    def _title_key(self, value):
        return normalize(re.sub(r"\b(?:folge|episode)\s*\d+\b", "", str(value or ""), flags=re.I))

    def _same_programme(self, left, right, tolerance_minutes=4):
        left_start = left.get("start")
        right_start = right.get("start")
        if not left_start or not right_start:
            return False
        try:
            delta = abs(
                (
                    datetime.fromisoformat(left_start)
                    - datetime.fromisoformat(right_start)
                ).total_seconds()
            )
        except Exception:
            return False
        if delta > tolerance_minutes * 60:
            return False

        left_title = self._title_key(left.get("title"))
        right_title = self._title_key(right.get("title"))
        if not left_title or not right_title:
            return delta <= 60
        if left_title == right_title:
            return True
        shorter, longer = sorted((left_title, right_title), key=len)
        return len(shorter) >= 5 and shorter in longer

    def _merge_programme_metadata(self, preferred, alternate):
        merged = dict(preferred)
        for key in ("title", "subtitle", "desc", "category", "icon", "end"):
            current = str(merged.get(key) or "").strip()
            candidate = str(alternate.get(key) or "").strip()
            if not current and candidate:
                merged[key] = alternate.get(key)
            elif key == "desc" and len(candidate) > len(current):
                merged[key] = alternate.get(key)
        return merged

    def _merge_program_lists(self, existing, incoming):
        merged = [dict(item) for item in (existing or []) if item.get("start")]

        for item in incoming or []:
            if not item.get("start"):
                continue
            match_index = next(
                (
                    index
                    for index, current in enumerate(merged)
                    if self._same_programme(current, item)
                ),
                None,
            )
            if match_index is None:
                merged.append(dict(item))
                continue

            current = merged[match_index]
            if self._programme_score(item) > self._programme_score(current):
                merged[match_index] = self._merge_programme_metadata(item, current)
            else:
                merged[match_index] = self._merge_programme_metadata(current, item)

        return sorted(merged, key=lambda item: item.get("start") or "")

    def _source_quality_metrics(self, channels, url, latest_end):
        available = [channel for channel in channels if channel.get("available")]
        main_available = [
            channel for channel in available if channel.get("preset")
        ]
        programme_count = sum(len(channel.get("programs") or []) for channel in available)
        return {
            "url": url,
            "ok": True,
            "coverage": (
                "broad"
                if len(available) >= 80 and len(main_available) >= 25
                else "partial"
            ),
            "channels": len(channels),
            "available_channels": len(available),
            "main_channels": len(main_available),
            "programmes": programme_count,
            "latest_end": latest_end.isoformat() if latest_end else None,
        }

    def _merge_channel_sets(self, channel_sets):
        merged = {}
        dynamic_names = {}

        for channels in channel_sets:
            for incoming in channels:
                channel_id = incoming.get("id")
                if not channel_id:
                    continue

                target_id = channel_id
                if not incoming.get("preset"):
                    name_key = normalize(incoming.get("source_name") or incoming.get("name"))
                    if name_key and name_key in dynamic_names:
                        target_id = dynamic_names[name_key]
                    elif name_key:
                        dynamic_names[name_key] = channel_id

                if target_id not in merged:
                    merged[target_id] = dict(incoming)
                    merged[target_id]["programs"] = list(incoming.get("programs") or [])
                    continue

                target = merged[target_id]
                for key in ("logo", "logo_light", "logo_dark", "source_name", "source_id"):
                    if not target.get(key) and incoming.get(key):
                        target[key] = incoming[key]

                target["programs"] = self._merge_program_lists(
                    target.get("programs") or [],
                    incoming.get("programs") or [],
                )
                target["available"] = bool(target["programs"])

        result = list(merged.values())
        result.sort(key=lambda ch: (
            0 if ch.get("preset") else 1,
            ch.get("order", 99999) if ch.get("preset") else 99999,
            str(ch.get("name") or "").casefold(),
        ))
        return result

    def refresh(self, force=False):
        with self.lock:
            self.refresh_running = True
            self.last_refresh_attempt = time.time()
            self.options = load_options()
            errors = []

            try:
                if not force and self._cache_fresh():
                    self.last_error = None
                    return

                successful_sets = []
                successful_urls = []
                latest_end = None
                source_metrics = []

                for index, url in enumerate(self._candidate_urls(), start=1):
                    try:
                        print(
                            f"[TV Guide] Lade EPG-Quelle {index}/{len(self._candidate_urls())}: {url}",
                            flush=True,
                        )
                        self._download(url)
                        parsed_channels = self._parse()
                        self._validate_feed_quality(parsed_channels)
                        successful_sets.append(parsed_channels)
                        successful_urls.append(url)

                        source_latest = (
                            datetime.fromisoformat(self.feed_latest_end)
                            if self.feed_latest_end else None
                        )
                        if source_latest and (latest_end is None or source_latest > latest_end):
                            latest_end = source_latest
                        source_metrics.append(
                            self._source_quality_metrics(
                                parsed_channels,
                                url,
                                source_latest,
                            )
                        )
                    except Exception as exc:
                        errors.append(f"{url}: {exc}")
                        source_metrics.append({
                            "url": url,
                            "ok": False,
                            "error": str(exc),
                            "channels": 0,
                            "available_channels": 0,
                            "main_channels": 0,
                            "programmes": 0,
                            "latest_end": None,
                        })
                        print(
                            f"[TV Guide] EPG-Quelle übersprungen: {url} -> {exc}",
                            flush=True,
                        )

                if not successful_sets:
                    self.last_error = (
                        " | ".join(errors) if errors else "Keine EPG-Quelle verfügbar."
                    )
                    print(f"[TV Guide] EPG-Fehler: {self.last_error}", flush=True)
                    return

                merged = self._merge_channel_sets(successful_sets)
                self.source_metrics = source_metrics
                self.channels = self._supplement_missing_channels(merged)
                self.feed_latest_end = latest_end.isoformat() if latest_end else None
                self.last_loaded = datetime.now().astimezone().isoformat()
                self.last_error = None
                self._save_parsed_cache("multi-source")

                available = sum(1 for ch in self.channels if ch.get("available"))
                main_available = sum(
                    1 for ch in self.channels
                    if ch.get("preset") and ch.get("available")
                )
                print(
                    f"[TV Guide] EPG zusammengeführt: {len(successful_urls)} Quellen, "
                    f"{available} Sender mit Programmdaten, "
                    f"{main_available}/50 Hauptsender",
                    flush=True,
                )
                if errors:
                    print(
                        "[TV Guide] Einzelne EPG-Quellen fehlgeschlagen: "
                        + " | ".join(errors),
                        flush=True,
                    )
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
        prefs = load_channel_preferences()
        by_id = {ch["id"]: ch for ch in self.channels}

        main_ids = [
            ch["id"]
            for ch in sorted(CHANNELS["channels"], key=lambda x: x["order"])
            if ch["id"] in by_id
        ]
        custom_ids = [
            channel_id
            for channel_id in prefs["order"]
            if channel_id in by_id and channel_id not in set(prefs["hidden"])
        ]

        max_channels = ui.get("max_channels", 0)
        if max_channels > 0:
            main_ids = main_ids[:max_channels]
            custom_ids = custom_ids[:max_channels]

        payload_ids = []
        for channel_id in [*main_ids, *custom_ids]:
            if channel_id in by_id and channel_id not in payload_ids:
                payload_ids.append(channel_id)

        channels = [dict(by_id[channel_id]) for channel_id in payload_ids]
        now = datetime.now().astimezone()
        global_latest = (
            datetime.fromisoformat(self.feed_latest_end)
            if self.feed_latest_end else None
        )
        source_success = any(metric.get("ok") for metric in self.source_metrics)

        for channel in channels:
            logo_light, logo_dark = normalized_logo_urls(channel)
            channel["logo_normalized_light"] = logo_light
            channel["logo_normalized_dark"] = logo_dark

            programmes = channel.get("programs") or []
            latest = None
            for item in programmes:
                try:
                    value = datetime.fromisoformat(item.get("end") or "")
                except Exception:
                    continue
                if latest is None or value > latest:
                    latest = value

            channel["data_latest_end"] = latest.isoformat() if latest else None
            if not programmes:
                channel["data_state"] = "no_programmes" if source_success else "source_unavailable"
                channel["data_message"] = (
                    "Für diesen Sender liegen aktuell keine Programmdaten vor."
                    if source_success
                    else "Die Programmdatenquellen sind derzeit nicht erreichbar."
                )
            elif latest and latest < now:
                channel["data_state"] = "ended"
                channel["data_message"] = "Die Programmdaten dieses Senders sind abgelaufen."
            elif global_latest and latest and latest < global_latest - timedelta(hours=6):
                channel["data_state"] = "ends_early"
                channel["data_message"] = "Die Programmdaten dieses Senders enden früher als bei den übrigen Sendern."
            else:
                channel["data_state"] = "ok"
                channel["data_message"] = ""

        return {
            "generated_at": datetime.now().astimezone().isoformat(),
            "profile": CHANNELS["profile"],
            "group": CHANNELS["group"],
            "provider": "XMLTV",
            "source_url": "multi-source",
            "sources": BUILTIN_EPG_URLS,
            "source_metrics": self.source_metrics,
            "official_metrics": self.official_metrics,
            "official_provider_count": sum(
                1 for item in OFFICIAL_PROVIDER_AUDIT.values() if item
            ),
            "official_provider_missing": [
                channel_id
                for channel_id, provider in OFFICIAL_PROVIDER_AUDIT.items()
                if not provider
            ],
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
            "channel_preferences": prefs,
            "main_channel_ids": main_ids,
            "custom_channel_ids": custom_ids,
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
        if "/api/channel-logo/" in path:
            match = re.search(r"/api/channel-logo/([^/]+)/(light|dark)\.svg$", path)
            if not match:
                self.send_error(404)
                return
            channel_id = unquote(match.group(1))
            theme = match.group(2)
            channel = next((item for item in STORE.channels if item.get("id") == channel_id), None)
            if not channel:
                self.send_error(404)
                return
            logo_path = normalized_logo_path(channel, theme)
            if not logo_path:
                self.send_error(404)
                return
            data = logo_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
            self.send_header("Cache-Control", "public, max-age=86400")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path.endswith("/api/guide") or path == "/api/guide":
            return self._json(STORE.payload())
        if path.endswith("/api/channels") or path == "/api/channels":
            return self._json(CHANNELS)
        if path.endswith("/api/channel-settings") or path == "/api/channel-settings":
            prefs = load_channel_preferences()
            selected = set(prefs["order"])
            hidden = set(prefs["hidden"])
            channel_info = [
                {
                    "id": ch["id"],
                    "logo_normalized_light": normalized_logo_urls(ch)[0],
                    "logo_normalized_dark": normalized_logo_urls(ch)[1],
                    "name": ch["name"],
                    "logo_file": ch.get("logo_file"),
                    "logo_file_light": ch.get("logo_file_light"),
                    "logo": ch.get("logo"),
                    "logo_light": ch.get("logo_light"),
                    "logo_dark": ch.get("logo_dark"),
                    "base_order": ch.get("order", 99999),
                    "preset": bool(ch.get("preset")),
                    "catalog_group": ch.get("catalog_group") or "Weitere Sender",
                    "available": bool(ch.get("available")),
                    "source_id": ch.get("source_id"),
                    "selected": ch["id"] in selected and ch["id"] not in hidden,
                }
                for ch in STORE.channels
            ]
            channel_info.sort(key=lambda ch: (
                0 if ch["selected"] else 1,
                0 if ch["preset"] else 1,
                ch["base_order"] if ch["preset"] else 99999,
                ch["name"].casefold(),
            ))
            return self._json({
                **prefs,
                "channels": channel_info,
                "catalog_count": len(channel_info),
            })
        if path.endswith("/api/settings") or path == "/api/settings":
            ui = load_options_ui()
            options = load_options()
            return self._json({
                "default_view": ui["default_view"],
                "columns_desktop": ui["columns_desktop"],
                "max_channels": ui["max_channels"],
                "theme_mode": ui["theme_mode"],
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
                "source_url": "multi-source",
                "sources": BUILTIN_EPG_URLS,
                "source_metrics": STORE.source_metrics,
                "official_metrics": STORE.official_metrics,
                "official_provider_count": sum(
                    1 for item in OFFICIAL_PROVIDER_AUDIT.values() if item
                ),
                "official_provider_missing": [
                    channel_id
                    for channel_id, provider in OFFICIAL_PROVIDER_AUDIT.items()
                    if not provider
                ],
                "last_loaded": STORE.last_loaded,
                "feed_latest_end": STORE.feed_latest_end,
                "error": STORE.last_error,
                "cache_exists": PARSED_CACHE_FILE.exists(),
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
                if max_channels < 0 or max_channels > 500:
                    return self._json({"ok": False, "error": "Angezeigte Sender muss zwischen 0 und 500 liegen."}, status=400)
                if refresh_minutes < 30 or refresh_minutes > 1440:
                    return self._json({"ok": False, "error": "EPG-Aktualisierung muss zwischen 30 und 1440 Minuten liegen."}, status=400)

                theme_mode = str(payload.get("theme_mode") or "auto").lower()
                if theme_mode not in {"auto", "dark", "light"}:
                    return self._json({"ok": False, "error": "Ungültige Darstellung."}, status=400)

                notification_service = str(payload.get("notification_service") or "").strip().lower()
                if not re.match(r"^[a-z0-9_]+\.[a-z0-9_]+$", notification_service):
                    return self._json({"ok": False, "error": "Ungültiger Benachrichtigungsdienst."}, status=400)

                try:
                    current_refresh_minutes = int(
                        current_raw.get("refresh_minutes") or DEFAULT_REFRESH_MINUTES
                    )
                except Exception:
                    current_refresh_minutes = DEFAULT_REFRESH_MINUTES

                refresh_needed = refresh_minutes != current_refresh_minutes

                new_options = {
                    "default_view": default_view,
                    "columns_desktop": columns,
                    "max_channels": max_channels,
                    "theme_mode": theme_mode,
                    "refresh_minutes": refresh_minutes,
                    "notification_service": notification_service,
                }
                update_addon_options(new_options)

                # The Supervisor stores the add-on options, but the mounted
                # /data/options.json of the already running container is not
                # guaranteed to be refreshed synchronously. Persist the same
                # validated options locally before answering the UI so a
                # subsequent GET immediately returns the just-saved values.
                save_options_file(new_options)

                STORE.options = {
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
