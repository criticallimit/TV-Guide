# TV Guide

Nach der Installation kann **TV Guide** über den Home-Assistant-Ingress geöffnet werden.

## Programmdaten

TV Guide lädt echte XMLTV-Daten. Als Standardquelle wird ab Version 0.2.3 der aktuelle deutsche HD+-Guide von iptv-org verwendet.

Veraltete Feeds werden automatisch erkannt, wenn ihre Programmdaten nicht mehr bis zur aktuellen Zeit reichen.

## Konfiguration

- **Standardansicht**: Jetzt, 20:15 oder 22:00
- **Spalten am Desktop**: 3 bis 6
- **EPG URL**: URL zu einer XMLTV- oder XMLTV-GZIP-Datei
- **Aktualisierungsintervall**: 30 bis 1440 Minuten

Der EPG-Feed wird persistent in `/data` zwischengespeichert. Ist die Quelle vorübergehend nicht erreichbar, verwendet das Add-on den zuletzt erfolgreich gespeicherten Feed weiter.

## Standardquelle

`https://iptv-org.github.io/epg/guides/de/hd-plus.de.xml`

Die Quelle lässt sich jederzeit austauschen, ohne die Oberfläche oder die feste Senderreihenfolge zu verändern.
