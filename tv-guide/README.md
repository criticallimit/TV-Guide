# TV Guide

Home-Assistant-Ingress-App/Add-on für eine kompakte Fernsehzeitschrift.

## Version 0.2.0

TV Guide verwendet jetzt echte XMLTV-Programmdaten.

Standardmäßig ist der deutsche XMLTV-Feed von FreeEPG eingetragen:

`https://www.free-epg.de/api/epg/de.xml.gz`

Der Feed kann in der Add-on-Konfiguration durch eine andere XMLTV-URL ersetzt werden.

### Enthalten

- Ingress-Oberfläche
- Ansichten Jetzt, 20:15 und 22:00
- fünf Sender pro Reihe auf Desktop
- responsive Mobilansicht
- laufende Sendung mit Fortschrittsbalken
- Detailansicht mit EPG-Beschreibung und Kategorie
- Senderlogos, sofern der XMLTV-Feed sie liefert
- feste Standard-Senderreihenfolge
- XMLTV-Sender-Mapping über Namen, Aliase und XMLTV-IDs
- lokaler EPG-Cache
- automatische Aktualisierung
- Weiterverwendung des letzten Cache-Stands bei einem Provider-Ausfall

Die Senderreihenfolge bleibt unabhängig vom verwendeten EPG-Anbieter fest.
