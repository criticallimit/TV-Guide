# Country catalogues

The application keeps the original German catalogue and storage filenames.
Other countries use their own catalogue, namespaced channel IDs, preferences,
download cache and parsed cache. An already running refresh remains attached to
its original country. Switching back reuses that country's store.

## Open-EPG fallback

The public XMLTV feeds from https://www.open-epg.com/app/epgguide.php are used
as a community fallback for every currently supported country:

| Country | Open-EPG feed |
| --- | --- |
| Germany | germany.xml.gz |
| Austria | austria.xml.gz |
| Switzerland | switzerland2.xml.gz |
| Netherlands | netherlands.xml.gz |
| Belgium | belgium.xml.gz |
| Norway | norway.xml.gz |
| France | france.xml.gz |

Open-EPG is deliberately assigned the lowest community-source priority. Direct
broadcaster data, broadcaster teletext and verified secondary web schedules
therefore win whenever they overlap the same programme slot. Germany also tries
the existing independent XMLTV source before Open-EPG.

To avoid unnecessary load on Open-EPG, each country keeps its own validated raw
Open-EPG cache. A successful Open-EPG download is reused for up to 24 hours.
If Open-EPG is temporarily unavailable, the last downloaded raw file is tried
again and must still pass the normal XMLTV freshness and quality checks before
its programmes can be used.

Additional XMLTV channels remain opt-in. Country namespaces prevent a channel
from one feed from being mixed into another country's configured catalogue.

## Direct broadcaster schedules

Direct-source endpoints are listed in countries.json. Current verified provider
families include ORF, SRG SSR, NPO, Play, VRT, VTM, NRK, TV 2 Norway and selected
French broadcasters, plus the German broadcaster and teletext sources.

Broadcaster programmes outrank community feeds. Date, station, timezone and
interval checks apply before merging. Missing or unavailable direct data falls
back to the country's XMLTV data; it is never labelled as official. These
sources do not guarantee coverage for every discovered channel or future date.
A missing station/date remains visibly unavailable instead of reusing an
undated schedule.
