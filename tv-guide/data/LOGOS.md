# Channel logos

`logo_library.json` maps each country-specific channel identity to two bundled SVG files. Both use the same 260 × 64 canvas and transparent padding. Main-channel catalogues point to these files directly; additional channels use the same identity map. Existing cached feed icons cannot override this map.

The library includes the six supported countries' feed catalogues. A catalogue entry does not imply that current programme data is available. Original artwork comes from the channel feeds, broadcasters' public websites and the public `tv-logo/tv-logos` collection. The asset entries record source URLs and hashes. Original German assets retain their existing provenance in `logo_manifest.json`.

Channel names and marks belong to their respective owners. Colour emblems remain recognisable; wordmarks use contrast appropriate to the background. No outline or shadow is added. Where an original cannot be verified or obtained, the entry explicitly uses `kind: name` with a readable channel name in both themes. Such entries are distinguishable from brand assets in the manifest. All configured main channels have brand assets.

The library is shipped with the app and needs no external image server at runtime. Newly discovered channels outside the shipped catalogue retain the existing logo fallback until added to a later library update.
