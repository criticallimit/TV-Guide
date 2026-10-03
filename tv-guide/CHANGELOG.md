# Changelog

## 0.2.8

- EPGShare-ID-Mapping für Das Erste und Tele 5 ergänzt
- kombinierter EPG-Kanal `SWR/SR.de` kann jetzt gleichzeitig SWR und SR versorgen
- fehlende Sender werden im Log namentlich ausgegeben
- Multi-Mapping eines XMLTV-Kanals auf mehrere interne Sender unterstützt


## 0.2.7

- automatische kostenlose EPG-Fallback-Kette eingeführt
- Primärquelle bleibt PrinzMichiDE/free-epg-germany
- Fallback: EPGShare01 Deutschland (DE1)
- jede Quelle wird auf Erreichbarkeit und Aktualität geprüft, bevor sie verwendet wird
- veraltete oder fehlerhafte Quellen werden automatisch übersprungen
- Cache kann von jeder gültigen Quelle stammen und bleibt providergebunden
- aktive Quelle wird im Status/API ausgegeben


## 0.2.6

- nicht erreichbare iptv-org Guide-URL entfernt
- Standard-EPG auf den vorhandenen deutschen XMLTV-GZIP-Feed von PrinzMichiDE/free-epg-germany umgestellt
- frühere eingebaute FreeEPG/iptv-org-URLs werden automatisch migriert
- fehlgeschlagene EPG-Downloads werden nur noch alle 5 Minuten erneut versucht statt bei jedem API-Aufruf


## 0.2.5

- korrigierte iptv-org Deutschland-EPG-URL auf `hd-plus.de.xml`
- fehlerhafte frühere `.epg.xml`-Standard-URL wird automatisch migriert
- behebt HTTP 404 beim EPG-Download


## 0.2.4

- EPG-Cache wird jetzt an die verwendete Provider-URL gebunden
- bei Wechsel der EPG-Quelle wird der alte Cache sofort verworfen
- behebt, dass nach dem Wechsel von FreeEPG weiterhin der alte, veraltete Feed eingelesen wurde
- Log zeigt nun explizit Quellewechsel und erfolgreichen Download der neuen Quelle


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
