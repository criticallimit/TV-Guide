# Legal source audit

Status: 2026-10-05

This document is a project-maintenance record, not legal advice. It records
licensing and rights issues that should be checked before adding, changing or
commercialising data sources or bundled assets.

## Status legend

- **Green**: project-owned material or a sufficiently clear licence for the
  intended repository use was identified.
- **Yellow**: publicly accessible and technically usable, but no sufficiently
  explicit redistribution/reuse licence was identified during this review.
- **Red**: published terms contain restrictions that can conflict with the
  project's current or potential use. Do not expand this use without permission
  or a separate legal basis.

## Project code

**Green — project-authored source code**

The repository now carries an MIT License for project-authored source code and
documentation. Third-party data, broadcaster material, logos and trademarks are
excluded from that licence by `THIRD_PARTY_NOTICES.md`.

The production Python backend uses the Python standard library. The container is
based on the Home Assistant base Python image. No separately vendored Python
package was identified in this review.

## EPG/XMLTV sources

### Open-EPG

**Yellow**

The service publicly advertises free XML EPG URLs. During this review no clear,
repository-wide licence was found that expressly grants unrestricted
redistribution, sublicensing or relicensing of the programme database.

Current project use downloads the feed at runtime. The project must not describe
Open-EPG data as MIT-licensed or bundle a persistent copy of the feed into a
release unless the applicable rights are confirmed.

Source: https://www.open-epg.com/app/epgguide.php

### EPGshare

**Yellow**

EPGshare publishes directly downloadable XMLTV files and documentation for use
as EPG feeds. During this review no explicit licence covering redistribution or
relicensing of the programme data was identified.

The project should therefore treat the service as an external runtime source,
not as project-owned or MIT-licensed data.

Source: https://epgshare01.online/

### EPG.PW

**Red if activated**

The code contains an `EPGPW_EPG_URL` constant, but it is not part of the
current `BUILTIN_EPG_URLS` list.

EPG.PW's published Terms of Service state that, except as provided by its terms,
content appearing through the site may not be copied, modified, published,
transmitted, distributed, displayed or sold. Do not make EPG.PW a built-in
source unless its terms are reviewed for the exact intended use or permission is
obtained.

Terms: https://epg.pw/terms.html

## Broadcaster websites, APIs and teletext

### ARD / ARD Mediathek

**Red / permission should be clarified**

The ARD Online terms state that ARD Mediathek and ARD Sounds content is
copyright-protected and that reproduction, modification, rearrangement,
republication, distribution or storage of information or data requires prior
written consent from the producing broadcaster. The offers are described as for
private, non-commercial use.

The project currently parses programme information from ARD programme pages and
some ARD-family teletext/programme pages. This should not be expanded on the
assumption that a publicly reachable page is automatically reusable.

Terms:
https://www.ard.de/die-ard/footer/nutzungsbedingungen-ard-online-100.html

### ZDF / ZDFtext

**Red / permission should be clarified**

ZDF's terms state that its online content is copyright-protected and that
reproduction, modification, distribution or storage of information or data,
including text and text fragments, requires prior written consent. The online
offer is described as private and non-commercial use.

The project currently parses ZDF programme information and ZDF teletext pages.
That use should be clarified before it is relied on as a long-term redistributable
data source.

Terms: https://www.zdf.de/nutzungsbedingungen

### SRG SSR

**Red for unrestricted use**

The SRG Developer Portal terms allow raw data for research and development,
prohibit commercial use, require source attribution, restrict passing raw data
to third parties, restrict storage unless expressly permitted, and require prior
written consent for SRG graphical elements.

The application currently uses public SRG integration-layer programme endpoints
rather than an authenticated Developer Portal key. The published Developer
Portal terms therefore cannot simply be assumed to license that endpoint or the
project's exact use. Treat SRG data as restricted unless the applicable terms
for the endpoint are confirmed.

Terms:
https://developer.srgssr.ch/sites/default/files/2024-11/Terms_SRGSSR_APIPortal_ENG_SRGRD_041624_1.pdf

### Other broadcasters

**Yellow until individually verified**

The project also contains direct or parsed programme sources for ORF, NPO, VRT,
VTM/DPG, Play, NRK, TV 2 Norway, TF1, M6, France Télévisions, ARTE and various
German commercial broadcasters. Public accessibility alone is not a licence.
Each source should be reviewed before commercialisation or before substantially
increasing automated retrieval, caching or redistribution.

## Channel logos

### tv-logo/tv-logos

**Red / replace or obtain clearer rights for bundled redistribution**

A substantial part of the bundled logo library traces to
`tv-logo/tv-logos`. The upstream repository currently has no repository-wide
`LICENSE` file. Its README describes the collection as free for personal use,
asks for attribution for redistribution, refers to a mixture of CC BY-SA and
CC BY-NC-SA licences, states that the project does not own the logos, and asks
services wishing to link to the logo collection to contact the maintainer.

The TV Guide repository converts and bundles many of these marks as local SVG
theme variants. Because no per-logo licence map establishes which logo is under
which licence, the entire bundled collection must not be presented as MIT
licensed.

Recommended long-term resolution:

1. replace uncertain third-party logos with text-only channel-name fallbacks;
2. retain a logo only where a clear permission/licence can be documented for
   that specific asset; or
3. obtain permission for the intended bundled redistribution.

Upstream: https://github.com/tv-logo/tv-logos

The current provenance records remain in
`tv-guide/data/logo_manifest.json` and `tv-guide/data/LOGOS.md`.

## Programme titles and descriptions

**Yellow to red depending on source and text**

Times, dates and other bare facts are different from creative editorial text.
The project currently imports programme titles, subtitles and, where supplied,
descriptions from XMLTV feeds and broadcaster sources. Longer descriptions may
be independently copyright-protected.

Until a source expressly permits redistribution of editorial descriptions, the
safer architecture is to minimise copied descriptive text and avoid treating it
as project-owned data.

## Trademark and affiliation statement

Channel names and logos are used to identify television services. They remain
the property of their respective owners. TV Guide must not imply endorsement,
official status or affiliation with a broadcaster or programme-data provider.

The repository now states this in `THIRD_PARTY_NOTICES.md`.

## Commercialisation

Do not add paid access, advertising, sponsorship tied to broadcaster content, or
other commercial exploitation on the assumption that the current source rights
permit it. Several reviewed terms expressly restrict use to non-commercial
purposes.

## Maintainer rule for new sources

Before merging a new source, record:

1. source/operator;
2. exact endpoint;
3. applicable terms or licence URL;
4. whether automated retrieval is permitted;
5. whether caching/storage is permitted;
6. whether redistribution is permitted;
7. whether commercial use is permitted;
8. attribution requirements;
9. rights status of logos/images/descriptions.

If these points cannot be established, mark the source **Yellow** and do not
represent it as freely licensed.
