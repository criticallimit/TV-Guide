# Country catalogues

The application keeps the original German catalogue and storage filenames.
Other countries use their own catalogue, namespaced channel IDs, preferences,
download cache and parsed cache. An already running refresh remains attached to
its original country. Switching back reuses that country's store.

The public feeds published at https://www.open-epg.com/app/epgguide.php are used as the country baselines. The established catalogues were checked against their feed IDs and programmes on 2026-10-04; Denmark was added on 2026-10-05 from the published Denmark feed and established Danish XMLTV identifiers:

| Country | Main channels | Feed | Direct broadcaster schedules |
| --- | ---: | --- | --- |
| Austria | 26 | austria.xml.gz | ORF 1, ORF 2, ORF III, ORF SPORT+ |
| Switzerland | 32 | switzerland2.xml.gz | SRF 1, SRF zwei, SRF info, RTS 1, RTS 2, RSI LA 1, RSI LA 2 |
| Netherlands | 20 | netherlands.xml.gz | No verified public parser configured |
| Belgium | 20 | belgium.xml.gz | Play, Play Actie, Play Fictie, Play Reality, Play Crime |
| Denmark | 18 | denmark.xml.gz | No verified public parser configured |
| Sweden | 16 | sweden1.xml.gz | SVT1, SVT2, SVT Barn, Kunskapskanalen, SVT24 |

For the catalogues that received a live programme verification, all main channels had programmes for the current date.
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

## Main-channel ordering

The built-in "Hauptsender" order is curated from established national TV-guide
sites. These sites are reference material for selection and ordering only; EPG
data continues to come from the configured programme sources. Stable channel
IDs and XMLTV IDs are not changed when the display order is revised.

- Germany: Hörzu is authoritative for the built-in order.
- Austria: TV-MEDIA and tvheute.at are compared; the shared national/generalist
  core is ranked first, with the remaining existing channels kept afterwards.
- Switzerland: Swiss domestic services remain grouped first because the market
  is multilingual; SRF's programme guide and Swiss TV-guide listings are used
  as cross-checks rather than forcing a German-language-only order.
- Netherlands: TVgids.nl and TV-Gids.net are compared.
- Belgium: Mijn-TV-Gids and GuideTV.be are compared across the Dutch- and
  French-language channel groups.
- France: Télé 7 Jours / programme-television.org is compared with the current
  national TNT ordering; only channels already present in the catalogue are
  ordered.
- Norway: VG TV-guide and the Norwegian TVguide/ZapTV listing are compared.
- Sweden: TV.nu, Tv-Tabla and OmTV are compared.
- Denmark: TVguide.dk is the primary national guide and is cross-checked against
  Danish channel line-ups; only existing catalogue channels are reordered.

When sources disagree, nationally prominent generalist/public channels shared by
multiple guides win over specialist, news, sport or pay-TV channels. Existing
catalogue membership is preserved unless a separate, verified catalogue change
is made.

## Sweden

Sweden uses the public `sweden1.xml.gz` feed as the stable primary source. The curated main list contains 16 national channels. The official SVT programme guide at `https://www.svtplay.se/kanaler` was verified on 2026-10-05. The add-on reads its dated day view only for the five SVT services listed above, validates the requested station and date, applies the `Europe/Stockholm` timezone and keeps the XMLTV feed as fallback.

## Denmark

Denmark uses the public `denmark.xml.gz` feed as its primary source. The curated main list contains 18 current national channels and uses explicit Danish XMLTV IDs to avoid cross-country fuzzy matches. No broadcaster endpoint is treated as official until a stable public schedule interface has been verified; the remaining channels in the feed stay available as opt-in channels.
