# TV Guide

Home-Assistant-Ingress-App/Add-on für eine klassische Fernsehprogramm-Übersicht mit echten XMLTV-Daten.

## Enthalten

- 38 vorkonfigurierte deutsche Hauptsender
- Ansichten Jetzt, 20:15, 22:00 und freie Zeitwahl
- lokale Senderlogos
- laufende Sendung mit Fortschrittsbalken und Restzeit
- Detailansicht mit Beschreibung, Untertitel und Kategorie
- responsive Mobilansicht
- automatische Home-Assistant-Theme-Anpassung
- 3 bis 6 Senderkarten pro Reihe auf Desktop
- persistenter XMLTV- und geparster EPG-Cache
- frei konfigurierbare XMLTV-Quelle
- robuste Senderzuordnung über IDs, Namen und Aliase
- persönliche Senderreihenfolge und Ausblenden einzelner Sender
- geräteübergreifende Merkliste
- TV-Erinnerungen 5, 10, 15 oder 30 Minuten vor Sendungsbeginn
- konfigurierbarer Home-Assistant-Benachrichtigungsdienst
- Testfunktion für den eingestellten Benachrichtigungsdienst

## Standard-EPG

`https://epgshare01.online/epgshare01/epg_ripper_DE1.xml.gz`

Der Feed kann in der Add-on-Konfiguration durch eine andere XMLTV- oder XMLTV-GZIP-URL ersetzt werden.

## Persistente Daten

TV Guide speichert benutzerbezogene Einstellungen und Laufzeitdaten ausschließlich im Add-on-Datenspeicher unter `/data`:

- `tv_guide_channel_order.json`
- `tv_guide_bookmarks.json`
- `tv_guide_reminders.json`
- `tv_guide_epg.xml.gz`
- `tv_guide_epg_parsed.json`

Dadurch bleiben Senderreihenfolge, Merkliste, Erinnerungen und EPG-Cache bei Add-on-Neustarts und Updates erhalten.
