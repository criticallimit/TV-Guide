from pathlib import Path
from urllib.request import Request, urlopen
from io import BytesIO
from PIL import Image, ImageChops
import json
import os

BASE = Path(__file__).resolve().parent
CHANNELS = json.loads((BASE / "data" / "channels.json").read_text(encoding="utf-8"))
TARGET = BASE / "www" / "logos"
TARGET.mkdir(parents=True, exist_ok=True)

CANVAS_W = 220
CANVAS_H = 64
PADDING_X = 10
PADDING_Y = 6
MAX_W = CANVAS_W - 2 * PADDING_X
MAX_H = CANVAS_H - 2 * PADDING_Y

failed = []

def crop_visible(img):
    img = img.convert("RGBA")
    alpha = img.getchannel("A")
    bbox = alpha.getbbox()
    if bbox:
        return img.crop(bbox)
    return img

def normalize_logo(raw):
    with Image.open(BytesIO(raw)) as source:
        img = crop_visible(source)

    # Some source files have nearly invisible antialiasing outside the actual logo.
    # Crop a second time after thresholding the alpha channel.
    alpha = img.getchannel("A")
    mask = alpha.point(lambda p: 255 if p >= 12 else 0)
    bbox = mask.getbbox()
    if bbox:
        img = img.crop(bbox)

    if img.width <= 0 or img.height <= 0:
        raise ValueError("Logo enthält keine sichtbaren Pixel")

    scale = min(MAX_W / img.width, MAX_H / img.height)
    new_size = (
        max(1, round(img.width * scale)),
        max(1, round(img.height * scale)),
    )
    img = img.resize(new_size, Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    x = (CANVAS_W - img.width) // 2
    y = (CANVAS_H - img.height) // 2
    canvas.alpha_composite(img, (x, y))
    return canvas

for channel in CHANNELS["channels"]:
    url = str(channel.get("logo_url") or "").strip()
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

        logo = normalize_logo(raw)
        tmp = path.with_suffix(".tmp")
        logo.save(tmp, format="PNG", optimize=True)
        os.replace(tmp, path)
        print(
            f"[TV Guide build] Logo normalisiert: {channel['name']} "
            f"-> {CANVAS_W}x{CANVAS_H}",
            flush=True,
        )
    except Exception as exc:
        failed.append(channel["name"])
        print(f"[TV Guide build] Logo fehlgeschlagen: {channel['name']} -> {exc}", flush=True)

if failed:
    raise SystemExit("Fehlende Senderlogos: " + ", ".join(failed))

print(
    f"[TV Guide build] {len(CHANNELS['channels'])} Senderlogos "
    f"zugeschnitten und fest ins Add-on-Paket übernommen.",
    flush=True,
)
