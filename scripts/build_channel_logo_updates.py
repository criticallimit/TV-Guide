"""Rebuild reviewed offline logos from pinned source bytes or bundled artwork.

Install Pillow for this build tool. Network access is opt-in (--download), never
part of the add-on runtime. Source hashes prevent silently shipping changed art.
"""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def prepare(raw):
    with Image.open(io.BytesIO(raw)) as original:
        image = original.convert("RGBA")
    bounds = image.getbbox()
    if not bounds:
        raise ValueError("Empty artwork")
    image = image.crop(bounds)
    # Twice the displayed area keeps high-density screens sharp without shipping
    # oversized broadcaster originals inside both SVG variants.
    image.thumbnail((500, 112), Image.Resampling.LANCZOS)
    stream = io.BytesIO()
    image.save(stream, format="PNG", optimize=True)
    normalized = stream.getvalue()
    sample = image.copy()
    sample.thumbnail((64, 64))
    visible = [sample.getpixel((x, y)) for y in range(sample.height) for x in range(sample.width)
               if sample.getpixel((x, y))[3] >= 24]
    if not visible:
        raise ValueError("Artwork has no visible pixels")
    luminance = sum((.2126*r + .7152*g + .0722*b)*alpha for r, g, b, alpha in visible) / sum(p[3] for p in visible)
    encoded = base64.b64encode(normalized).decode("ascii")
    variants = {}
    for theme in ("light", "dark"):
        # A backing plate preserves white/black broadcaster artwork faithfully.
        plate = ""
        if theme == "light" and luminance >= 190:
            plate = '<rect x="2" y="2" width="256" height="60" rx="5" fill="#253041"/>'
        elif theme == "dark" and luminance <= 65:
            plate = '<rect x="2" y="2" width="256" height="60" rx="5" fill="#f4f6fa"/>'
        variants[theme] = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 260 64" '
                           f'width="260" height="64" data-tv-guide-theme="{theme}">{plate}'
                           f'<image href="data:image/png;base64,{encoded}" x="5" y="4" '
                           'width="250" height="56" preserveAspectRatio="xMidYMid meet"/></svg>\n')
    return normalized, variants


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    root = args.repo_root / "tv-guide"
    manifest = json.loads((root / "data/logo_updates.json").read_text(encoding="utf-8"))
    manifest["channels"] = {}
    for part in manifest["source_parts"]:
        entries = json.loads((root / "data" / part).read_text(encoding="utf-8"))["channels"]
        if manifest["channels"].keys() & entries.keys():
            raise ValueError(f"Duplicate reviewed channel identities: {part}")
        manifest["channels"].update(entries)
    library_file = root / "data/logo_library.json"
    library = json.loads(library_file.read_text(encoding="utf-8"))
    europe = json.loads((root / "data/europe_logo_library.json").read_text(encoding="utf-8"))
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    generated = {}
    # Build direct artwork first so explicit reuse can refer to newly added marks.
    for channel_id, update in sorted(manifest["channels"].items(), key=lambda pair: "reuse_channel" in pair[1]):
        if "source_url" in update:
            url = update["source_url"]
            cached = args.cache_dir / (digest(url.encode()) + ".image")
            if not cached.exists() and args.download:
                with urlopen(Request(url, headers={"User-Agent": "TV-Guide logo preparation"}), timeout=30) as response:
                    raw = response.read(8_000_001)
                if len(raw) > 8_000_000:
                    raise ValueError(f"Oversized artwork: {channel_id}")
                cached.write_bytes(raw)
            raw = cached.read_bytes()
            if digest(raw) != update["source_sha256"]:
                raise ValueError(f"Source artwork changed: {channel_id}")
            if update["source_sha256"] not in generated:
                normalized, variants = prepare(raw)
                asset_id = "acquired-" + digest(normalized)[:20]
                for theme, svg in variants.items():
                    target = root / f"www/logos/library/{theme}/{asset_id}.svg"
                    target.write_text(svg, encoding="utf-8")
                generated[update["source_sha256"]] = asset_id
                library["assets"][asset_id] = {
                    "source": url, "sha256": digest(raw), "normalized_sha256": digest(normalized),
                    "mime": "image/png", "snapshot_date": manifest["snapshot_date"],
                    "treatments": {"light": "Original artwork; dark plate for pale marks",
                                   "dark": "Original artwork; light plate for dark marks"},
                }
            asset_id = generated[update["source_sha256"]]
            artwork = {"asset": asset_id, "light": f"logos/library/light/{asset_id}.svg",
                       "dark": f"logos/library/dark/{asset_id}.svg"}
        elif "reuse_channel" in update:
            source = library["channels"][update["reuse_channel"]]
            if source["kind"] != "brand":
                raise ValueError(f"Cannot reuse text fallback: {channel_id}")
            artwork = {key: source[key] for key in ("asset", "light", "dark")}
        else:
            source_id = update["reuse_europe_asset"]
            source = europe["assets"][source_id]
            raw = (root / "www" / source["local_asset"]).read_bytes()
            if digest(raw) != source["source_sha256"]:
                raise ValueError(f"Bundled source changed: {channel_id}")
            normalized, variants = prepare(raw)
            asset_id = "acquired-" + digest(normalized)[:20]
            for theme, svg in variants.items():
                (root / f"www/logos/library/{theme}/{asset_id}.svg").write_text(svg, encoding="utf-8")
            artwork = {"asset": asset_id, "light": f"logos/library/light/{asset_id}.svg",
                       "dark": f"logos/library/dark/{asset_id}.svg"}
            library["assets"][asset_id] = {
                "source": source["source_project"] + ":" + source["source_path"],
                "source_commit": source["source_commit"], "sha256": digest(raw),
                "normalized_sha256": digest(normalized), "mime": "image/png",
                "treatments": {"light": "Original artwork with contrast backing as needed",
                               "dark": "Original artwork with contrast backing as needed"},
            }
        library["channels"][channel_id] = {
            **{key: update[key] for key in ("country", "name", "source_ids", "main")},
            "kind": "brand", "reviewed_update": manifest["snapshot_date"], **artwork,
        }
    # Keep the established registry intact. Small explicit addition parts make
    # later source reviews and updates manageable, without changing selection.
    items = [(key, library["channels"][key]) for key in manifest["channels"]]
    manifest["library_parts"] = []
    for start in range(0, len(items), 64):
        channels = dict(items[start:start+64])
        assets = {entry["asset"]: library["assets"][entry["asset"]]
                  for entry in channels.values() if entry["asset"].startswith("acquired-")}
        name = f"logo_updates/library-{start//64:03}.json"
        (root / "data" / name).write_text(
            json.dumps({"channels": channels, "assets": assets}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        manifest["library_parts"].append(name)
    manifest.pop("channels")
    (root / "data/logo_updates.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    path = root / "data/logo_manifest.json"
    aggregate = json.loads(path.read_text(encoding="utf-8"))
    for code in json.loads((root / "data/countries.json").read_text(encoding="utf-8")):
        entries = [e for e in library["channels"].values() if e["country"] == code]
        aggregate["countries"][code] = {"channels": len(entries), "main_channels": sum(e["main"] for e in entries),
                                         "name_fallbacks": sum(e["kind"] == "name" for e in entries)}
    path.write_text(json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Applied {len(items)} reviewed channel logo assignments.")


if __name__ == "__main__":
    main()
