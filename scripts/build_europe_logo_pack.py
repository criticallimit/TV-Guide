#!/usr/bin/env python3
"""Build the offline Europe-wide TV logo pack used by TV Guide.

Input is a checked-out snapshot of tv-logo/tv-logos. Output is committed to this
repository so Home Assistant never needs network access for channel artwork.
Third-party marks remain subject to THIRD_PARTY_NOTICES.md.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from pathlib import Path

EUROPE_DIRS = (
    "countries/albania",
    "countries/austria",
    "countries/belgium",
    "countries/bulgaria",
    "countries/croatia",
    "countries/czech-republic",
    "countries/france",
    "countries/germany",
    "countries/greece",
    "countries/hungary",
    "countries/ireland",
    "countries/italy",
    "countries/lithuania",
    "countries/luxembourg",
    "countries/malta",
    "countries/netherlands",
    "countries/nordic/denmark",
    "countries/nordic/finland",
    "countries/nordic/iceland",
    "countries/nordic/norway",
    "countries/nordic/sweden",
    "countries/poland",
    "countries/portugal",
    "countries/romania",
    "countries/russia",
    "countries/serbia",
    "countries/slovakia",
    "countries/slovenia",
    "countries/spain",
    "countries/switzerland",
    "countries/turkey",
    "countries/ukraine",
    "countries/united-kingdom",
    "countries/world-europe",
)

SKIP_PARTS = {"obsolete", "old", "screen-bug", "custom", "hd"}
CANVAS_W, CANVAS_H = 260, 64
PAD_X, PAD_Y = 5, 4

COUNTRY_FROM_PATH = {
    "albania":"al","austria":"at","belgium":"be","bulgaria":"bg","croatia":"hr",
    "czech-republic":"cz","france":"fr","germany":"de","greece":"gr","hungary":"hu",
    "ireland":"ie","italy":"it","lithuania":"lt","luxembourg":"lu","malta":"mt",
    "netherlands":"nl","denmark":"dk","finland":"fi","iceland":"is","norway":"no",
    "sweden":"se","poland":"pl","portugal":"pt","romania":"ro","russia":"ru",
    "serbia":"rs","slovakia":"sk","slovenia":"si","spain":"es","switzerland":"ch",
    "turkey":"tr","ukraine":"ua","united-kingdom":"gb","world-europe":"eu",
}

def clean_key(path: Path) -> str:
    stem = path.stem.lower()
    stem = re.sub(r"-(?:al|at|be|bg|hr|cz|fr|de|gr|hu|ie|it|lt|lu|mt|nl|dk|fi|is|no|se|pl|pt|ro|ru|rs|sk|si|es|ch|tr|ua|uk)$", "", stem)
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return stem

def svg_wrapper(asset_name: str, theme: str) -> str:
    # The raster/SVG artwork is stored once locally. Both theme wrappers are
    # tiny and reference that local file, so runtime network access is never
    # needed and the repository does not duplicate the source bytes.
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}" '
        f'width="{CANVAS_W}" height="{CANVAS_H}" data-tv-guide-theme="{theme}">'
        f'<image href="../assets/{asset_name}" x="{PAD_X}" y="{PAD_Y}" '
        f'width="{CANVAS_W-2*PAD_X}" height="{CANVAS_H-2*PAD_Y}" '
        'preserveAspectRatio="xMidYMid meet"/></svg>\n'
    )

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--repo-root", default=Path(__file__).resolve().parents[1], type=Path)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()

    source = args.source.resolve()
    root = args.repo_root.resolve()
    out = root / "tv-guide/www/logos/europe"
    assets = out / "assets"
    light = out / "light"
    dark = out / "dark"
    for folder in (assets, light, dark):
        folder.mkdir(parents=True, exist_ok=True)

    # Generated pack owns this directory completely.
    for folder in (assets, light, dark):
        for old in folder.iterdir():
            if old.is_file():
                old.unlink()

    candidates = []
    for rel in EUROPE_DIRS:
        folder = source / rel
        if not folder.is_dir():
            continue
        for path in folder.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                continue
            relative = path.relative_to(source)
            if SKIP_PARTS.intersection(relative.parts):
                continue
            country_dir = rel.split("/")[-1]
            country = COUNTRY_FROM_PATH[country_dir]
            candidates.append((country, relative.as_posix(), path))

    # One asset per exact source file; aliases let future country catalogues
    # resolve by normalized brand name without re-downloading artwork.
    entries = {}
    aliases = {}
    hashes = {}
    for country, rel, path in sorted(candidates, key=lambda row: row[1]):
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        ext = path.suffix.lower()
        brand = clean_key(path)
        asset_id = hashlib.sha256((country + ":" + rel).encode("utf-8")).hexdigest()[:20]
        filename = asset_id + ".svg"
        asset_name = digest[:24] + ext
        asset_path = assets / asset_name
        if not asset_path.exists():
            asset_path.write_bytes(raw)

        (light / filename).write_text(svg_wrapper(asset_name, "light"), encoding="utf-8")
        (dark / filename).write_text(svg_wrapper(asset_name, "dark"), encoding="utf-8")

        entries[asset_id] = {
            "brand_key": brand,
            "countries": [country],
            "source_path": rel,
            "source_sha256": digest,
            "source_commit": args.source_commit,
            "source_project": "tv-logo/tv-logos",
            "local_asset": f"logos/europe/assets/{asset_name}",
            "light": f"logos/europe/light/{filename}",
            "dark": f"logos/europe/dark/{filename}",
        }
        aliases.setdefault(brand, []).append(asset_id)
        hashes.setdefault(digest, []).append(asset_id)

    registry = {
        "schema_version": 1,
        "scope": "Europe-wide offline channel-logo pack",
        "runtime_network_required": False,
        "source_project": "tv-logo/tv-logos",
        "source_commit": args.source_commit,
        "notice": "Third-party trademarks/assets are not MIT licensed; see THIRD_PARTY_NOTICES.md.",
        "canvas": {"width": CANVAS_W, "height": CANVAS_H, "padding_x": PAD_X, "padding_y": PAD_Y},
        "assets": entries,
        "aliases": aliases,
        "duplicate_source_hashes": {k:v for k,v in hashes.items() if len(v) > 1},
    }
    (root / "tv-guide/data/europe_logo_library.json").write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Generated {len(entries)} offline European logo assets.")

if __name__ == "__main__":
    main()
