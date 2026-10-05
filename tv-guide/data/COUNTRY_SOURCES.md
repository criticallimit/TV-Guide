# Country catalogues

The application keeps the original German catalogue and storage filenames.
Other countries use their own catalogue, namespaced channel IDs, preferences,
download cache and parsed cache. An already running refresh remains attached to
its original country. Switching back reuses that country's store.

The public feeds published at https://www.open-epg.com/app/epgguide.php were
checked against their actual channel IDs and programmes on 2026-10-04:

| Country | Main channels | Feed | Direct broadcaster schedules |
| --- | ---: | --- | --- |
| Austria | 26 | austria.xml.gz | ORF 1, ORF 2, ORF III, ORF SPORT+ |
| Switzerland | 32 | switzerland2.xml.gz | SRF 1, SRF zwei, SRF info, RTS 1, RTS 2, RSI LA 1, RSI LA 2 |
| Netherlands | 20 | netherlands.xml.gz | No verified public parser configured |
| Belgium | 20 | belgium.xml.gz | Play, Play Actie, Play Fictie, Play Reality, Play Crime |
| Sweden | 16 | sweden1.xml.gz | SVT1, SVT2, SVT Barn, Kunskapskanalen, SVT24 |

All main channels had programmes for the current date during verification.
Additional channels are discovered from the country's own feed and remain
opt-in. A source containing a shared international channel does not change the
country selection or import another country's catalogue.

Direct-source endpoints are listed in countries.json. They were verified from
the broadcasters' published programme pages and live responses:

- ORF: https://tv.orf.at/program/orf1/ (absolute broadcast timestamps and dated links).
- Swiss broadcasters: https://www.srf.ch/play/tv/programm-nach-sender (public SRG integration-layer requests with explicit station and date).
- Play: https://www.play.tv/tv-gids (dated, channel-specific schedule data).
- SVT: https://www.svtplay.se/kanaler (dated station sections via `?date=YYYY-MM-DD&range=day`).

Broadcaster programmes outrank community feeds. Date, station, timezone and
interval checks apply before merging. Missing or unavailable direct data falls
back to the country's public XMLTV feed; it is never labelled as official.
These sources do not guarantee coverage for every discovered channel or future
date. A missing station/date remains visibly unavailable instead of reusing an
undated schedule.

## Sweden

Sweden uses the public `sweden1.xml.gz` feed as the stable primary source. The curated main list contains 16 national channels. The official SVT programme guide at `https://www.svtplay.se/kanaler` was verified on 2026-10-05. The add-on reads its dated day view only for the five SVT services listed above, validates the requested station and date, applies the `Europe/Stockholm` timezone and keeps the XMLTV feed as fallback.
