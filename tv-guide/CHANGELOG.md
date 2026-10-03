# Changelog

## 0.2.3

- Standard-EPG auf den aktuellen iptv-org Deutschland/HD+ XMLTV-Feed umgestellt
- alte eingebaute FreeEPG-Standard-URL wird automatisch migriert
- veraltete EPG-Feeds werden anhand des letzten Sendungsendes erkannt und nicht mehr als aktuelle Daten angezeigt
- eigener benutzerdefinierter XMLTV-Link bleibt unverändert


## 0.2.2

- XMLTV-Zeitstempel toleranter verarbeitet
- Programmdaten werden nicht mehr vorzeitig durch ein Zeitfenster herausgefiltert
- Diagnose im Log: gemappte Sender, Gesamtzahl Programme, Trefferzahl und EPG-Zeitraum
- klarere Statusmeldung bei 0 gefundenen Programmen


## 0.2.1

- Ingress-Webserver startet jetzt sofort
- EPG-Download und XMLTV-Verarbeitung laufen beim Start im Hintergrund
- verhindert den Home-Assistant-Fehler „App scheint noch nicht bereit zu sein“
- Status zeigt an, wenn EPG-Daten noch geladen werden


## 0.2.0

- echte XMLTV/EPG-Anbindung
- FreeEPG Deutschland als vorkonfigurierte Standardquelle
- XMLTV-GZIP-Unterstützung
- persistenter EPG-Cache
- einstellbares Aktualisierungsintervall
- robustes Sender-Mapping mit Aliasen und XMLTV-IDs
- EPG-Beschreibung, Untertitel und Kategorie in der Detailansicht
- Senderlogos aus dem XMLTV-Feed
- Fallback auf Cache-Daten bei Provider-Ausfall
- Statusanzeige für erkannte Sender

## 0.1.0

- erstes installierbares Home-Assistant-App/Add-on
- Ingress-Oberfläche
- Jetzt-, 20:15- und 22:00-Ansicht
- feste Senderreihenfolge
- responsive Darstellung
- Demo-EPG für den UI-Prototyp
