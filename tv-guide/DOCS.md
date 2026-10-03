# TV Guide

Nach der Installation kann **TV Guide** über den Home-Assistant-Ingress geöffnet werden.

## Programmdaten

TV Guide lädt echte XMLTV-Daten. Als Standardquelle wird ab Version 0.2.3 der aktuelle deutsche HD+-Guide von PrinzMichiDE/free-epg-germany verwendet.

Veraltete Feeds werden automatisch erkannt, wenn ihre Programmdaten nicht mehr bis zur aktuellen Zeit reichen.

## Konfiguration

- **Standardansicht**: Jetzt, 20:15 oder 22:00
- **Spalten am Desktop**: 3 bis 6
- **EPG URL**: URL zu einer XMLTV- oder XMLTV-GZIP-Datei
- **Aktualisierungsintervall**: 30 bis 1440 Minuten

Der EPG-Feed wird persistent in `/data` zwischengespeichert. Ist die Quelle vorübergehend nicht erreichbar, verwendet das Add-on den zuletzt erfolgreich gespeicherten Feed weiter.

## Standardquelle

`https://raw.githubusercontent.com/PrinzMichiDE/free-epg-germany/main/epg3.xml.gz`

Die Quelle lässt sich jederzeit austauschen, ohne die Oberfläche oder die feste Senderreihenfolge zu verändern.


## Kostenlose Fallback-Quelle

Falls die konfigurierte/primäre EPG-Quelle nicht erreichbar oder veraltet ist, prüft TV Guide automatisch den kostenlosen Deutschland-Feed von EPGShare01:

`https://epgshare01.online/epgshare01/epg_ripper_DE1.xml.gz`

Nur ein Feed, dessen Programmdaten die aktuelle Zeit abdecken, wird übernommen.


## Radio Bremen TV

Falls der XMLTV-Feed Radio Bremen TV nicht enthält, ergänzt TV Guide den Sender aus der offiziellen Programmübersicht der ARD Mediathek:

`https://www.ardmediathek.de/radiobremen/programm/YYYY-MM-DD`

Es werden der aktuelle Tag und zwei Folgetage geladen. Dadurch bleibt auch dieser Sender kostenlos und ohne kommerzielle EPG-API verfügbar.
