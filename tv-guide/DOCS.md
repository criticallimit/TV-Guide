# TV Guide

Nach der Installation kann **TV Guide** über den Home-Assistant-Ingress geöffnet werden.

## Programmdaten

Ab Version 0.2.0 lädt TV Guide echte XMLTV-Daten. Standardmäßig wird der deutsche Feed von FreeEPG verwendet.

## Konfiguration

- **Standardansicht**: Jetzt, 20:15 oder 22:00
- **Spalten am Desktop**: 3 bis 6
- **EPG URL**: URL zu einer XMLTV- oder XMLTV-GZIP-Datei
- **Aktualisierungsintervall**: 30 bis 1440 Minuten

Der EPG-Feed wird persistent in `/data` zwischengespeichert. Ist die Quelle vorübergehend nicht erreichbar, verwendet das Add-on den zuletzt erfolgreich gespeicherten Feed weiter.

## Standardquelle

`https://www.free-epg.de/api/epg/de.xml.gz`

Die Quelle lässt sich jederzeit austauschen, ohne die Oberfläche oder die feste Senderreihenfolge zu verändern.
