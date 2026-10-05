# Channel logos

`logo_library.json` maps each country-specific channel identity to two bundled SVG files. Both use the same 260 × 64 canvas and transparent padding. Main-channel catalogues point to these files directly; additional channels use the same identity map. Existing cached feed icons cannot override this map.

The library includes the six supported countries' feed catalogues. A catalogue entry does not imply that current programme data is available. Original artwork comes from the channel feeds, broadcasters' public websites and the public `tv-logo/tv-logos` collection. The asset entries record source URLs and hashes. Original German assets retain their existing provenance in `logo_manifest.json`.

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
