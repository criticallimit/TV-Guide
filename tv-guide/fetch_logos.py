from pathlib import Path
from urllib.request import Request, urlopen
import json
import os

BASE = Path(__file__).resolve().parent
CHANNELS = json.loads((BASE / "data" / "channels.json").read_text(encoding="utf-8"))
MANIFEST = json.loads((BASE / "data" / "logo_manifest.json").read_text(encoding="utf-8"))
TARGET = BASE / "www" / "logos"
TARGET.mkdir(parents=True, exist_ok=True)

failed = []

manifest_by_id = {item["id"]: item for item in MANIFEST["channels"]}

for channel in CHANNELS["channels"]:
    entry = manifest_by_id.get(channel["id"], {})
    url = str(entry.get("url") or channel.get("logo_url") or "").strip()

    if not url:
        failed.append(channel["name"])
        continue

    path = TARGET / f"{channel['id']}.png"
    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0 HomeAssistant-TV-Guide-Build",
        "Accept": "image/png,image/*;q=0.8,*/*;q=0.1",
    })

    try:
        with urlopen(req, timeout=30) as response:
            raw = response.read(4 * 1024 * 1024 + 1)

        if not raw or len(raw) > 4 * 1024 * 1024:
            raise ValueError("ungültige Dateigröße")
        if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Quelle liefert keine PNG-Datei")

        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(raw)
        os.replace(tmp, path)
        print(f"[TV Guide build] Logo gespeichert: {channel['name']}", flush=True)
    except Exception as exc:
        failed.append(channel["name"])
        print(f"[TV Guide build] Logo fehlgeschlagen: {channel['name']} -> {exc}", flush=True)

if failed:
    raise SystemExit("Fehlende Senderlogos: " + ", ".join(failed))

print(
    f"[TV Guide build] {len(CHANNELS['channels'])} Senderlogos fest ins Add-on-Paket übernommen.",
    flush=True,
)
