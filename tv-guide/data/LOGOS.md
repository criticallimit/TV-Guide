# Channel logos

`logo_library.json` and the reviewed additions listed in `logo_updates.json` map country-specific channel identities to two bundled SVG files. Both use the same 260 × 64 canvas and transparent padding. Main-channel catalogues point to these files directly; additional channels use the same identity map. Existing cached feed icons cannot override this map.

The library covers feed identities across the countries configured in `countries.json`. A catalogue entry does not imply that current programme data is available. Original artwork comes from the channel feeds, broadcasters' public websites and the public `tv-logo/tv-logos` collection. The asset entries record source URLs and hashes. Original German assets retain their existing provenance in `logo_manifest.json`.

Channel names and marks belong to their respective owners. Colour emblems remain recognisable; wordmarks use contrast appropriate to the background. No outline or shadow is added. Where an original cannot be verified or obtained, the entry explicitly uses `kind: name` with a readable channel name in both themes. Such entries are distinguishable from brand assets in the manifest. All configured main channels have brand assets.

The library is shipped with the app and needs no external image server at runtime. Newly discovered channels outside the shipped catalogue retain the existing logo fallback until added to a later library update.


## Europe-wide offline pack

TV Guide also ships a generated Europe-wide logo pack under `www/logos/europe`.
The pack is built from a pinned snapshot of `tv-logo/tv-logos` and currently
contains 4,967 European channel marks. Each source image is stored locally once,
with separate prebuilt light and dark SVG wrappers. The wrappers use a shared
260 × 64 canvas and add only a restrained contrast plate when luminance analysis
shows that a very light or very dark mark would otherwise disappear against the
selected theme.

The application resolves bundled country-specific assets first, then this
Europe-wide offline pack, and finally a local text fallback. Runtime HTTP
downloads for channel logos are disabled.

The generated registry is `data/europe_logo_library.json`. It records source
paths, hashes, source commit, aliases and local light/dark paths so future
country catalogues can reuse existing assets without another logo search.

## Reviewed channel additions

`logo_updates.json` indexes the reviewed channel assignments added in October 2026,
with small source and prepared-library parts under `data/logo_updates/`. These record
original source URLs and SHA-256 hashes, exact XMLTV identities, reused
bundled artwork and rejected feed images. Additional sources were discovered via
[iptv-org/api](https://github.com/iptv-org/api); this catalogue is a discovery aid,
not a guarantee that an image is the correct broadcaster mark. Placeholder images
and visibly unrelated branding were excluded after visual review.

`python scripts/build_channel_logo_updates.py --cache-dir /path/to/logo-cache`
rebuilds the additions from cached original images. Add `--download` to fetch
missing originals at build time; changed source hashes fail the build and require
a new review. Pillow is required only by the build tool. Original alpha bounds
are cropped, oversized files reduced to at most twice the displayed size, duplicate prepared PNGs shared, and brand
colours preserved. White and black marks receive contrast backing where needed.
The resulting light/dark SVGs are self-contained and remain fully offline.

All UK main channels now resolve to broadcaster artwork, including E4, Film4,
More4 and 5USA. Some additional channels still lack verifiable artwork, especially
obsolete feed identities, ambiguous names and unavailable sources. Newly added
XMLTV channels can therefore still display a text fallback.
