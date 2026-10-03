# Changelog

## 0.4.0

- Oberfläche grundlegend als klassische TV-Zeitschrift neu aufgebaut
- zentrale Schnellwahl JETZT / 20:15 / 22:00 / ANDERE ZEIT
- horizontale Tagesleiste für heute plus sieben Folgetage
- Senderkarten mit Logo-Spalte, Uhrzeit, Titel, Genre und Pfeil zur Detailansicht
- laufende Sendung mit JETZT-Markierung, Restzeit und Fortschrittsbalken
- mobile Darstellung als kompakte Sender-/Programmzeilen
- Sendungen können lokal im Browser gemerkt und wieder entfernt werden
- eigene TV-Guide-Marke statt Übernahme geschützter HÖRZU-Markenassets
- vorhandene EPG-, Detail- und Home-Assistant-Ingress-Funktionen bleiben erhalten


## 0.3.2

- Senderköpfe und Programmkarten optisch näher an einer klassischen TV-Zeitschrift
- laufende Sendung deutlich hervorgehoben
- "JETZT"-Kennzeichnung, Beginn/Ende und Restzeit ergänzt
- Fortschrittsbalken verfeinert
- kompaktere Darstellung der Folgesendungen
- Fallback-Senderkopf für Feeds ohne Logo verbessert
- Kartenabstände, Rahmen und Hover-Zustände überarbeitet


## 0.3.1

- "Andere Zeiten" ist jetzt vollständig funktionsfähig
- Datum und beliebige Uhrzeit können direkt in der TV-Guide-Oberfläche gewählt werden
- Standardansicht aus den Home-Assistant-App-Einstellungen wird jetzt tatsächlich angewendet
- konfigurierte Desktop-Spaltenzahl (3–6) wird jetzt von der Oberfläche übernommen
- Detailansicht zeigt zusätzlich den Sendetag
- Navigation und responsive Darstellung weiter an die klassische TV-Zeitschrift angeglichen


## 0.3.0

- Radio Bremen TV wird nicht mehr über den unzuverlässigen MagentaTV-Fallback ergänzt
- stattdessen wird die offizielle Programmübersicht der ARD Mediathek für Radio Bremen verwendet
- lädt heute plus zwei Folgetage kostenlos und ohne API-Schlüssel
- Sendungsende wird aus dem Beginn der jeweils folgenden Sendung abgeleitet
- EPGShare bleibt die Hauptquelle für die übrigen 19 Sender


## 0.2.9

- Radio Bremen TV wird bei fehlenden XMLTV-Daten über den kostenlosen MagentaTV-Web-EPG ergänzt
- verwendet den von MagentaTV selbst bereitgestellten Web-Guide-Endpunkt
- Radio Bremen ist dort als Kanal-ID 368 geführt
- EPGShare bleibt Primärquelle für die übrigen Sender
- MagentaTV-Ergänzung fällt bei Fehlern sauber zurück, ohne den restlichen Guide zu blockieren


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
