"""Optional Home Assistant state publishing, isolated from HTTP and EPG workers."""
import json
import os
import threading
import time
from datetime import timedelta
from urllib.error import HTTPError
from urllib.request import Request

from .json_files import read_json_file, write_json_file

SENSOR_OPTIONS = {
    "sensor_next_reminder": ("sensor.tv_guide_next_reminder", "Nächste Erinnerung", "mdi:alarm", "timestamp"),
    "sensor_bookmark_count": ("sensor.tv_guide_bookmark_count", "Gemerkte Sendungen", "mdi:bookmark", None),
    "sensor_reminder_count": ("sensor.tv_guide_reminder_count", "Ausstehende Erinnerungen", "mdi:alarm-check", None),
    "sensor_last_update": ("sensor.tv_guide_last_update", "Letzte EPG-Aktualisierung", "mdi:update", "timestamp"),
    "sensor_refresh_running": ("binary_sensor.tv_guide_refresh_running", "EPG-Aktualisierung läuft", "mdi:sync", None),
}
SOURCE = "criticallimit/TV-Guide"


class SensorPublisher:
    def __init__(self, runtime):
        self.runtime = runtime
        self.wake = threading.Event()
        self.path = runtime.OPTIONS_FILE.with_name("tv_guide_sensor_states.json")
        valid_ids = {definition[0] for definition in SENSOR_OPTIONS.values()}
        self.managed = {item for item in read_json_file(self.path, []) if isinstance(item, str) and item in valid_ids}
        self.published = {}
        self.checked_at = {}

    def _manage(self, entity_id, enabled):
        updated = self.managed | {entity_id} if enabled else self.managed - {entity_id}
        if updated != self.managed:
            # Persist ownership before POST, so a restart can still remove disabled states.
            write_json_file(self.path, sorted(updated))
            self.managed = updated

    def _api(self, entity_id, token, method="GET", payload=None):
        request = Request(
            "http://supervisor/core/api/states/" + entity_id,
            method=method,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None,
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        )
        try:
            with self.runtime.urlopen(request, timeout=3) as response:
                raw = response.read(256 * 1024)
            return json.loads(raw) if raw else None
        except HTTPError as error:
            if error.code == 404 and method in {"GET", "DELETE"}:
                return None
            raise

    def _values(self, now):
        runtime = self.runtime
        pending = []
        for item in runtime.load_reminders():
            try:
                start = runtime.datetime.fromisoformat(item["start"])
                end = runtime.datetime.fromisoformat(item["end"])
                if start.utcoffset() is None or end.utcoffset() is None:
                    continue
                minutes = max(0, min(180, int(item.get("minutes", 10))))
                if not item.get("sent") and end > now and start + timedelta(minutes=5) > now:
                    pending.append((start - timedelta(minutes=minutes), item, start, minutes))
            except (ValueError, TypeError, KeyError, AttributeError):
                continue
        pending.sort(key=lambda entry: entry[0])
        next_state, next_attributes = "unknown", {}
        if pending:
            due, reminder, start, minutes = pending[0]
            next_state = due.isoformat()
            next_attributes = {
                "reminder_id": str(reminder.get("id", ""))[:300],
                "channel": str(reminder.get("channel", ""))[:120],
                "channel_id": str(reminder.get("channelId", ""))[:120],
                "title": str(reminder.get("title", ""))[:240],
                "programme_start": start.isoformat(),
                "minutes_before": minutes,
            }
        loaded = runtime.STORE.last_loaded
        try:
            loaded = runtime.datetime.fromisoformat(loaded).astimezone(runtime.EPG_TIMEZONE).isoformat()
        except (ValueError, TypeError):
            loaded = "unknown"
        return {
            "sensor_next_reminder": (next_state, next_attributes),
            "sensor_bookmark_count": (str(len(runtime.clean_bookmarks(runtime.load_bookmarks()))), {}),
            "sensor_reminder_count": (str(len(pending)), {}),
            "sensor_last_update": (loaded, {}),
            "sensor_refresh_running": ("on" if runtime.STORE.refresh_running else "off", {}),
        }

    def publish_once(self):
        runtime = self.runtime
        options = runtime.load_options()
        if not any(options.get(key) for key in SENSOR_OPTIONS) and not self.managed:
            return
        token = os.environ.get("SUPERVISOR_TOKEN", "")
        if not token:
            return
        values = self._values(runtime.datetime.now(runtime.EPG_TIMEZONE))
        language = runtime.effective_language(options.get("language"))
        for key, (entity_id, name, icon, device_class) in SENSOR_OPTIONS.items():
            enabled = options.get(key, False)
            if not enabled and entity_id not in self.managed:
                continue
            state, extra = values[key]
            attributes = {"friendly_name": "TV Guide · " + runtime.translate(name, language),
                          "icon": icon, "tv_guide_source": SOURCE, **extra}
            if device_class:
                attributes["device_class"] = device_class
            desired = {"state": state, "attributes": attributes}
            if enabled and self.published.get(entity_id) == desired and time.monotonic() - self.checked_at.get(entity_id, float("-inf")) < 60:
                continue
            try:
                existing = self._api(entity_id, token)
                owned = isinstance(existing, dict) and existing.get("attributes", {}).get("tv_guide_source") == SOURCE
                # Settings may have changed while the Core request was pending.
                if runtime.load_options().get(key, False) != enabled:
                    continue
                if existing is not None and not owned:
                    print(f"[TV Guide] Sensor-ID bereits anderweitig verwendet: {entity_id}", flush=True)
                    self.published.pop(entity_id, None)
                    if not enabled:
                        self._manage(entity_id, False)
                    continue
                if not enabled:
                    if owned:
                        self._api(entity_id, token, "DELETE")
                    self._manage(entity_id, False)
                    self.published.pop(entity_id, None)
                    continue
                self._manage(entity_id, True)
                if not owned or any(existing.get(attribute) != value for attribute, value in desired.items()):
                    self._api(entity_id, token, "POST", desired)
                self.published[entity_id] = desired
                self.checked_at[entity_id] = time.monotonic()
            except Exception as error:
                print(f"[TV Guide] Sensor konnte nicht synchronisiert werden ({entity_id}): {error}", flush=True)

    def run(self):
        while True:
            self.wake.clear()
            try:
                self.publish_once()
            except Exception as error:
                print(f"[TV Guide] Sensor-Synchronisierung fehlgeschlagen: {error}", flush=True)
            self.wake.wait(15)
