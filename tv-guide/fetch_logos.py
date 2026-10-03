from pathlib import Path
import base64
import json
import os

BASE = Path(__file__).resolve().parent
CHANNELS = json.loads((BASE / "data" / "channels.json").read_text(encoding="utf-8"))
SOURCE = BASE / "data" / "logos_source"
TARGET = BASE / "www" / "logos"
TARGET.mkdir(parents=True, exist_ok=True)

failed = []

for channel in CHANNELS["channels"]:
    src = SOURCE / f"{channel['id']}.png.b64"
    dst = TARGET / f"{channel['id']}.png"

    try:
        if not src.exists():
            raise FileNotFoundError(f"fehlende lokale Logoquelle: {src.name}")

        encoded = "".join(src.read_text(encoding="utf-8").split())
        raw = base64.b64decode(encoded, validate=True)

        if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("lokale Logoquelle ist keine PNG-Datei")

        tmp = dst.with_suffix(".tmp")
        tmp.write_bytes(raw)
        os.replace(tmp, dst)
        print(f"[TV Guide build] Lokales Logo eingebunden: {channel['name']}", flush=True)
    except Exception as exc:
        failed.append(channel["name"])
        print(f"[TV Guide build] Logo fehlgeschlagen: {channel['name']} -> {exc}", flush=True)

if failed:
    raise SystemExit("Fehlende Senderlogos: " + ", ".join(failed))

print(
    f"[TV Guide build] {len(CHANNELS['channels'])} Senderlogos vollständig lokal eingebunden.",
    flush=True,
)
