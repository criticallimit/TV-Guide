import base64
import hashlib
import html
import json
import os
import re
import sys
import threading
import time
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

from .api import GuideRequestHandler
from .json_files import read_json_file, write_json_file
from .personal_channels import PersonalChannels
from .programme_values import EPG_TIMEZONE as EPG_TIMEZONE
from .programme_values import feed_channel_id as feed_channel_id
from .programme_values import first_text as first_text
from .programme_values import normalize as normalize
from .programme_values import xmltv_datetime as xmltv_datetime
from .providers import ARD_PROGRAM_URL as ARD_PROGRAM_URL
from .providers import ARD_RB_PROGRAM_URL as ARD_RB_PROGRAM_URL
from .providers import BUILTIN_EPG_URLS as BUILTIN_EPG_URLS
from .providers import EPGPW_EPG_URL as EPGPW_EPG_URL
from .providers import EPGSHARE_EPG_URL as EPGSHARE_EPG_URL
from .providers import OFFICIAL_PROVIDER_BY_CHANNEL as OFFICIAL_PROVIDER_BY_CHANNEL
from .providers import OPEN_EPG_URL as OPEN_EPG_URL
from .providers import (
    SECONDARY_WEB_PROVIDER_BY_CHANNEL as SECONDARY_WEB_PROVIDER_BY_CHANNEL,
)
from .providers import SR_PROGRAM_URL as SR_PROGRAM_URL
from .providers import SWR_PROGRAM_URL as SWR_PROGRAM_URL
from .providers import TELETEXT_PROVIDER_BY_CHANNEL as TELETEXT_PROVIDER_BY_CHANNEL
from .providers import ZDF_PROGRAM_URL as ZDF_PROGRAM_URL
from .store import GuideStore

BASE = Path(__file__).resolve().parent.parent
WWW = BASE / "www"
CHANNELS = json.loads((BASE / "data" / "channels.json").read_text(encoding="utf-8"))
COUNTRIES = json.loads((BASE / "data" / "countries.json").read_text(encoding="utf-8"))
COUNTRY_CATALOGS = {
    code: json.loads((BASE / "data" / item["catalog"]).read_text(encoding="utf-8"))
    for code, item in COUNTRIES.items() if code != "de"
}
LOGO_LIBRARY = json.loads((BASE / "data" / "logo_library.json").read_text(encoding="utf-8"))
OPTIONS_FILE = Path("/data/options.json")
CACHE_FILE = Path("/data/tv_guide_epg.xml.gz")
PARSED_CACHE_FILE = Path("/data/tv_guide_epg_parsed.json")
PARSED_CACHE_SCHEMA_VERSION = 10
CHANNEL_PREFS_FILE = Path("/data/tv_guide_channel_order.json")
REMINDERS_FILE = Path("/data/tv_guide_reminders.json")
BOOKMARKS_FILE = Path("/data/tv_guide_bookmarks.json")
LOGO_CACHE_DIR = Path("/data/tv_guide_logos")
LOGO_RENDER_VERSION = 3
REMINDER_LOCK = threading.Lock()
BOOKMARK_LOCK = threading.Lock()


# Every curated main channel goes through the same official-source layer. Channels
# without a stable public schedule endpoint remain XMLTV-only until a verified
# official endpoint is added here; no guessed URLs are used.
OFFICIAL_PROVIDER_AUDIT = {
    channel_id: OFFICIAL_PROVIDER_BY_CHANNEL.get(channel_id)
    for channel_id in [ch["id"] for ch in CHANNELS["channels"]]
}


DEFAULT_REFRESH_MINUTES = 180

LANGUAGES = {"de", "en", "nl", "fr", "it", "nb"}
TRANSLATIONS = {
    code: json.loads((WWW / "locales" / f"{code}.json").read_text(encoding="utf-8"))
    for code in LANGUAGES
}
HA_LOCALE_CACHE = {"expires": 0, "value": {}}
HA_LOCALE_LOCK = threading.Lock()


def language_code(value):
    value = str(value or "").lower().replace("_", "-").split("-")[0]
    return "nb" if value == "no" else value if value in LANGUAGES else "en"


def home_assistant_locale():
    token = os.environ.get("SUPERVISOR_TOKEN", "")
    if not token:
        return {}
    with HA_LOCALE_LOCK:
        if HA_LOCALE_CACHE["expires"] > time.monotonic():
            return dict(HA_LOCALE_CACHE["value"])
        value = {}
        try:
            request = Request("http://supervisor/core/api/config", headers={"Authorization": f"Bearer {token}"})
            with urlopen(request, timeout=3) as response:
                config = json.loads(response.read(1024 * 1024).decode("utf-8"))
            value = {key: str(config[key]) for key in ["language", "country"] if config.get(key)}
        except Exception:
            # An unavailable Core must not prevent the guide from opening.
            pass
        HA_LOCALE_CACHE.update(expires=time.monotonic() + (300 if value else 30), value=value)
        return dict(value)


def effective_language(value=None):
    options = load_options()
    configured = value or options.get("language", "auto")
    if configured != "auto":
        return language_code(configured)
    locale = home_assistant_locale()
    if locale.get("language"):
        return language_code(locale["language"])
    country = str(locale.get("country") or options.get("country") or "de").lower()
    return {"de": "de", "at": "de", "nl": "nl", "no": "nb", "fr": "fr"}.get(country, "en")


def translate(message, language, **values):
    catalogue = TRANSLATIONS.get(language, TRANSLATIONS["en"])
    message = catalogue.get(message, TRANSLATIONS["en"].get(message, message))
    return re.sub(r"\{(\w+)\}", lambda match: str(values.get(match[1], match[0])), message)


def save_options_file(options):
    write_json_file(OPTIONS_FILE, options)


def country_code(value):
    value = str(value or "de").lower()
    return value if value in COUNTRIES else "de"


def country_file(path, country):
    # Preserve every existing German installation's file paths.
    return path if country == "de" else path.with_name(f"{country}_{path.name}")


def active_store(store=None):
    return store if store is not None else globals().get("STORE")


def channel_catalog(store=None):
    store = active_store(store)
    return store.catalog if store is not None else CHANNELS


def channel_preferences_file(store=None):
    store = active_store(store)
    return country_file(CHANNEL_PREFS_FILE, getattr(store, "country", "de"))


def load_options():
    data = read_json_file(OPTIONS_FILE, {})
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
        "country": country_code(data.get("country")),
        "language": data.get("language") if data.get("language") in LANGUAGES | {"auto"} else "auto",
        "refresh_minutes": max(30, min(1440, refresh)),
        "notification_service": notification_service,
    }

def load_options_ui():
    data = read_json_file(OPTIONS_FILE, {})
    default_view = str(data.get("default_view") or "now")
    if default_view not in {"now", "1800", "2015", "2200"}:
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


def base_channel_ids(store=None):
    return [ch["id"] for ch in sorted(channel_catalog(store)["channels"], key=lambda x: x["order"])]


def _logo_source_for_channel(channel, theme):
    bundled = LOGO_LIBRARY["channels"].get(str(channel.get("source_channel_id") or channel.get("id") or ""))
    if bundled and bundled.get(theme):
        return bundled[theme]
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
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="260" height="64" viewBox="0 0 260 64">
  <image x="5" y="4" width="250" height="56" preserveAspectRatio="xMidYMid meet"
         href="{image_href}"/>
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
    bundled = LOGO_LIBRARY["channels"].get(str(channel.get("source_channel_id") or channel.get("id") or ""))
    if bundled and source == bundled.get(theme):
        path = (WWW / source).resolve()
        if WWW.resolve() in path.parents and path.is_file():
            # Library assets already have the final canvas and theme treatment.
            return path
    source_identity = source or f"text:{channel.get('name') or channel.get('id') or 'TV'}"
    source_key_value = f"{LOGO_RENDER_VERSION}:{source_identity}"
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
    return (
        f"{base}/light.svg?v={LOGO_RENDER_VERSION}",
        f"{base}/dark.svg?v={LOGO_RENDER_VERSION}",
    )


def known_channel_ids(store=None):
    store = active_store(store)
    ids = set(base_channel_ids(store))
    if store is not None:
        ids.update(ch.get("id") for ch in getattr(store, "channels", []) if ch.get("id"))
    return ids

def merge_channel_order(saved_order, store=None):
    default_order = base_channel_ids(store)
    known = known_channel_ids(store)
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

def load_channel_preferences(store=None):
    raw = read_json_file(channel_preferences_file(store), {})

    order = merge_channel_order(raw.get("order"), store)
    known = known_channel_ids(store)
    hidden = [x for x in raw.get("hidden", []) if x in known]
    return {"order": order, "hidden": hidden}

def save_channel_preferences(order, hidden, store=None):
    known = known_channel_ids(store)
    clean_order = []
    for channel_id in order or []:
        if channel_id in known and channel_id not in clean_order:
            clean_order.append(channel_id)

    prefs = {
        "order": clean_order,
        "hidden": [x for x in hidden if x in known],
    }
    write_json_file(channel_preferences_file(store), prefs)
    return prefs

def reset_channel_preferences(store=None):
    try:
        channel_preferences_file(store).unlink()
    except FileNotFoundError:
        pass
    return {"order": base_channel_ids(store), "hidden": []}


def load_reminders():
    return read_json_file(REMINDERS_FILE, [])


def save_reminders(items):
    write_json_file(REMINDERS_FILE, items)


def load_bookmarks():
    return read_json_file(BOOKMARKS_FILE, [])


def save_bookmarks(items):
    write_json_file(BOOKMARKS_FILE, items)


def clean_bookmarks(items):
    now = datetime.now(EPG_TIMEZONE)
    result = []
    for item in items:
        try:
            end = datetime.fromisoformat(str(item.get("end") or "")).astimezone(EPG_TIMEZONE)
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

    start = datetime.fromisoformat(reminder["start"]).astimezone(EPG_TIMEZONE)
    language = effective_language(reminder.get("language"))
    message = translate("{channel}: „{title}“ beginnt um {time} Uhr.", language,
                        channel=reminder["channel"], title=reminder["title"], time=start.strftime("%H:%M"))
    body = {
        "title": translate("TV Guide – Erinnerung", language),
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
            now = datetime.now(EPG_TIMEZONE)
            changed = False
            with REMINDER_LOCK:
                reminders = load_reminders()
                kept = []
                for reminder in reminders:
                    try:
                        start = datetime.fromisoformat(reminder["start"]).astimezone(EPG_TIMEZONE)
                        end = datetime.fromisoformat(reminder["end"]).astimezone(EPG_TIMEZONE)
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

class EPGStore(GuideStore):
    """Store bound to the shared application services."""

    runtime = sys.modules[__name__]
STORE = EPGStore()
COUNTRY_STORES = {STORE.country: STORE}
SETTINGS_LOCK = threading.Lock()
PERSONAL_CHANNELS = PersonalChannels(sys.modules[__name__])

class Handler(GuideRequestHandler):
    """HTTP handler bound to the shared application services."""

    runtime = sys.modules[__name__]
def main():
    port = int(os.environ.get("PORT", "8099"))
    print(f"[TV Guide] Webserver startet sofort auf Port {port}", flush=True)
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    STORE.refresh_running = True
    threading.Thread(target=STORE.refresh, daemon=True).start()
    threading.Thread(target=reminder_worker, daemon=True).start()
    print("[TV Guide] Ingress ist bereit; EPG wird im Hintergrund geladen", flush=True)
    server.serve_forever()
