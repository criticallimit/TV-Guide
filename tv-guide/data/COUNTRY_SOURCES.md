# Country catalogues

The application keeps the original German catalogue and storage filenames.
Other countries use their own catalogue, namespaced channel IDs, preferences,
download cache and parsed cache. An already running refresh remains attached to
its original country. Switching back reuses that country's store.

The public feeds published at https://www.open-epg.com/app/epgguide.php are used as the country baselines. The established catalogues were checked against their feed IDs and programmes on 2026-10-04; Denmark was added on 2026-10-05 from the published Denmark feed and established Danish XMLTV identifiers:

| Country | Main channels | Feed | Direct broadcaster schedules |
| --- | ---: | --- | --- |
| Austria | 26 | austria.xml.gz | ORF services; nine existing commercial channels through Joyn Austria; shared public broadcasters |
| Switzerland | 32 | switzerland2.xml.gz | SRG services; seven existing CH Media channels; shared public broadcasters |
| Netherlands | 20 | netherlands.xml.gz | Six NPO services; TVgids.nl secondary schedules for eight RTL/SBS channels |
| Belgium | 20 | belgium.xml.gz | VRT, VTM and Play services; La Une, Tipik and La Trois through RTBF |
| Denmark | 18 | denmark.xml.gz | DR services directly; TV 2's public guide covers all 18 prepared channels |
| Sweden | 16 | sweden1.xml.gz | Five SVT services; TV4, Sjuan, TV12 and TV4 Fakta |

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

Denmark keeps `denmark.xml.gz` as its baseline and uses explicit Danish XMLTV IDs to avoid cross-country fuzzy matches. Direct DR schedules cover DR1, DR2 and DR Ramasjang. The public TV 2 guide supplies schedules for all 18 existing prepared channels, including a secondary source for those three DR services. TV 2 is the guide publisher for the other commercial channels; these are not individual direct integrations with each broadcaster.

## Additional public schedules checked on 2026-10-06

- **Denmark:** [DRTV guide](https://www.dr.dk/drtv/tv-guide) publishes requests to `https://prod95-cdn.dr-massive.com/api/schedules`. Numeric DR station IDs are used. [TV 2 guide](https://tvtid.tv2.dk/) publishes requests to `https://tvtid-api.api.tv2.dk/api/tvtid/v1/epg/dayviews`. Exact Danish station IDs and explicit epoch start/end times are used.
- **Austria:** [Joyn Austria's guide](https://www.joyn.at/play/live-tv) supplies ATV, ATV2, PULS 4, PULS 24, ServusTV, ProSieben Austria, SAT.1 Austria, Kabel Eins Austria and sixx Austria. Its public web-client API key is read from the current script URL at refresh time, rather than saved in add-on options or embedded in a release. Requests require both `Joyn-Country: AT` and `Joyn-Distribution-Tenant: JOYN_AT`; exact Austrian stream IDs prevent German schedule substitution. The web-client script layout remains an external dependency. A missing/changed key or GraphQL error leaves XMLTV/cache fallback available.
- **Belgium:** [RTBF's guide](https://www.rtbf.be/grille-des-programmes) publishes requests to `https://bff-service.rtbf.be/oaos/v1.6/schedulings`. The current channel IDs are La Une `1`, Tipik `33`, La Trois `3`. Programme start plus the published duration determines the end. RTL tvi/club/plug/district remain on their existing feed; no verified additional RTL Belgium adapter was activated.
- **Netherlands:** [TVgids.nl](https://www.tvgids.nl/gids/) supplies secondary schedules for RTL 4/5/7/8/Z, SBS6, SBS9 and Net 5. This is a guide publisher, not a newly verified direct RTL/Talpa endpoint. Shared two-channel pages use exact station slugs and column IDs, with explicit epoch start/end times; missing end times are discarded rather than guessed. Today's page uses the undated route; other days use an explicit date. Veronica's combined children's-channel variant is not changed by this addition.

Live reads through the actual backend returned dated schedules for 6–8 October for all 38 affected existing channels. This is a point-in-time technical check, not evidence of continuous availability or independent underlying databases. Existing countries, channel IDs, selections, logos and XMLTV feeds are retained. Shared responses and failed URLs are cached within one background refresh; opening Ingress or the card does not initiate these external requests. Date windows include the previous day for midnight carry-over and use local timezones, including 23/25-hour daylight-saving transitions.
