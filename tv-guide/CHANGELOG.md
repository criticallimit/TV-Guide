# Changelog

## 0.5.9

- Lovelace-Ladefehler nach Einführung des gemeinsamen Renderers behoben
- Loader wartet jetzt auf den gemeinsamen Renderer und registriert die Karte erst danach
- Lovelace-Karte greift explizit auf den global geladenen gemeinsamen Renderer zu

- Ingress und Lovelace verwenden jetzt denselben Renderer für Tagesleiste, Senderkarten und Programmlisten
- Lovelace lädt dieselbe Stylesheet-Datei wie die Ingress-Seite
- künftige optische Änderungen an der Programmübersicht müssen dadurch nicht mehr doppelt gepflegt werden

- Lovelace-Karte optisch an die Ingress-Ansicht angeglichen
- gleiche Kopfzeilenlogik mit linker Zeitauswahl und mittigem Programmtitel
- Tagesleiste, Hauptsender-Zeile, Senderköpfe, Programmkarten, JETZT-Markierung und Fortschrittsbalken übernommen
- fünf Folgesendungen pro Sender statt der vereinfachten Zwei-Zeilen-Darstellung

- Kartenwähler zeigt TV Guide jetzt als kompakte Auswahl statt die komplette Programmkarte als riesige Vorschau
- die eigentliche Lovelace-Karte bleibt nach dem Hinzufügen unverändert vollständig verfügbar

- geführte Lovelace-Einrichtung direkt im Zahnrad-Menü ergänzt
- Statusprüfung für Kartendatei und geladene TV-Guide-Karte
- Ressourcen-URL kann direkt kopiert und die Home-Assistant-Ressourcen-Seite geöffnet werden
- stabile Loader-Ressource `/local/tv-guide-card-loader.js` eingeführt, damit spätere Kartenupdates keine Änderung der registrierten Ressourcen-URL erfordern

- Konfigurationssymbol rechts in der Kopfzeile ergänzt
- Add-on-Einstellungen können jetzt direkt in der TV-Guide-Ingress-Oberfläche geändert werden
- Standardansicht, Spaltenzahl, Darstellung, EPG-Quelle, Aktualisierungsintervall und Benachrichtigungsdienst sind dort editierbar
- Programmtitel bleibt trotz linker Zeitauswahl und rechtem Konfigurationssymbol exakt mittig

- eigene auswählbare Lovelace-Karte „TV Guide“ ergänzt
- Karte registriert sich über `window.customCards` für den normalen Home-Assistant-Kartenwähler
- Add-on stellt Kartendatei, Senderlogos und eine kompakte Programmdatenansicht unter `/local` bereit
- Dashboard-Karte übernimmt persönliche Senderreihenfolge und ausgeblendete Sender
- Schnellwahl Jetzt / 20:15 / 22:00 direkt in der Lovelace-Karte
- README-Anleitung von Webpage-Karte auf die native auswählbare TV-Guide-Karte umgestellt

- README wieder etwas ausführlicher und stärker an der Nutzung orientiert
- Hinweis zur Anzeige in der Home-Assistant-Seitenleiste ergänzt
- kurze Anleitung zur Einbindung in ein Lovelace-Dashboard über eine Webseite/Webpage-Karte ergänzt
- technische Implementierungsdetails bleiben bewusst außerhalb der README

- README-Dateien bewusst auf kurze Nutzerbeschreibungen reduziert
- technische Detailauflistungen aus den README-Dateien entfernt

- veraltete README-Inhalte vollständig auf den aktuellen Funktionsstand gebracht
- alte Demo-/FreeEPG-Hinweise entfernt
- Installation, EPGShare-Standardquelle, persistente Daten, Senderanpassung, Merkliste und Erinnerungen dokumentiert

- Benachrichtigungsdienst kann direkt aus der Merkliste getestet werden
- Test verwendet exakt den in den Add-on-Einstellungen hinterlegten Home-Assistant-Dienst
- Oberfläche zeigt den tatsächlich verwendeten Dienst oder eine konkrete Fehlermeldung an

- Browser-Merkliste wird nur einmal migriert; danach ist der persistente Add-on-Speicher maßgeblich
- verhindert, dass auf einem anderen Gerät gelöschte Sendungen durch einen alten Browser-Cache wieder auftauchen
- Merkliste wird zusammen mit EPG und Erinnerungen regelmäßig zwischen geöffneten Home-Assistant-Clients synchronisiert

- Merkliste wird jetzt ebenfalls persistent im Add-on unter `/data/tv_guide_bookmarks.json` gespeichert
- gemerkte Sendungen sind dadurch auf allen Geräten mit demselben Home Assistant verfügbar
- vorhandene lokale Browser-Merkliste wird beim ersten Öffnen automatisch in den persistenten Speicher übernommen
- abgelaufene Einträge werden serverseitig bereinigt

- Dokumentation und Add-on-Übersetzungen an den aktuellen Stand angepasst
- veraltete Angaben zur früheren EPG-Standardquelle entfernt
- neue Optionen für Theme und Benachrichtigungsdienst dokumentiert
- Sender-Sortierung, persistenter EPG-Cache und Erinnerungen dokumentiert

- Benachrichtigungsdienst kann in den Add-on-Einstellungen über `notification_service` gewählt werden
- Standard ist `persistent_notification.create`; für Push aufs Smartphone kann z. B. ein vorhandener `notify.mobile_app_...`-Dienst eingetragen werden

- Home-Assistant-Erinnerungen für gemerkte Sendungen ergänzt
- pro Sendung wählbar: 5, 10, 15 oder 30 Minuten vorher
- Erinnerungen werden persistent unter `/data/tv_guide_reminders.json` gespeichert und funktionieren auch nach Add-on-Neustarts
- ein Hintergrund-Worker prüft die Erinnerungen alle 20 Sekunden
- zum Erinnerungszeitpunkt wird über die Home-Assistant-API eine persistente Home-Assistant-Benachrichtigung erzeugt
- das Add-on erhält dafür `homeassistant_api: true`
- gesetzte Erinnerungen werden in „Gemerkt“ mit ⏰ und Vorlaufzeit angezeigt
- wird eine gemerkte Sendung entfernt, wird auch ihre noch offene Erinnerung gelöscht

- Benutzer können die Senderreihenfolge jetzt selbst anpassen
- Standardsortierung bleibt unveränderter Standard und kann jederzeit wiederhergestellt werden
- Sortierung per Drag & Drop sowie mit Auf-/Ab-Pfeilen für Touch-Geräte
- einzelne Sender können ausgeblendet und später wieder eingeblendet werden
- persönliche Reihenfolge und Sichtbarkeit werden update-sicher persistent unter `/data/tv_guide_channel_order.json` gespeichert
- neue Sender werden in bestehende Benutzerlisten anhand ihrer Standardposition eingefügt

- solange eine EPG-Aktualisierung läuft, fragt die Oberfläche automatisch alle 1,5 Sekunden den aktuellen Stand ab
- dadurch wird nach einem Neustart zunächst der persistente Cache sofort gezeigt und kurz danach automatisch durch die frisch geladenen EPG-Daten ersetzt
- Statuszeile zeigt währenddessen „EPG wird im Hintergrund aktualisiert“

- Start-Nachladen korrekt in den eigentlichen Guide-Ladevorgang verschoben
- dadurch aktualisiert sich die Seite beim ersten Start automatisch, ohne dass der Benutzer einen Zeit-Button anklicken muss

- bei Uhrzeiten außerhalb des verfügbaren EPG-Zeitraums wird keine veraltete letzte Sendung mehr angezeigt
- stattdessen erscheint sauber „Für diese Zeit keine EPG-Daten verfügbar“

- persistenter, bereits geparster EPG-Cache unter `/data/tv_guide_epg_parsed.json`
- nach Add-on-Neustart wird das zuletzt gültige TV-Programm sofort angezeigt, während der EPG im Hintergrund aktualisiert wird
- Senderreihenfolge und aktuelle Sender-Metadaten werden beim Laden des Caches neu angewendet
- beim allerersten Start lädt die Oberfläche automatisch alle 1,5 Sekunden nach, solange der EPG noch aufgebaut wird

- Sender-Mapping priorisiert jetzt exakte XMLTV-IDs und exakte Alias-/Namens-Treffer
- unsichere kurze Fuzzy-Treffer werden nicht mehr geraten
- verhindert Fehlzuordnungen zwischen ähnlich benannten Sendern wie RTL, RTLup und RTLZWEI

- Programmtitel bleibt unabhängig von der Zeitauswahl exakt zentriert
- Zeitauswahl deutlich kompakter und links vor dem Titel positioniert

- blaue Kopfzeile vollständig entfernt
- Zeitauswahl direkt links vor dem Programmtitel „Das aktuelle TV-Programm jetzt“ angeordnet

- Kopfzeile entfernt; Zeitauswahl steht jetzt direkt vor dem Programmtitel
- Navigation ist nicht mehr als sticky Header ausgeführt

- Desktop-Spaltenzahl aus den Einstellungen wird jetzt im CSS tatsächlich verwendet
- `theme_mode` wird nun korrekt über die Guide-API an das Frontend übergeben

- Senderreihenfolge anhand der aktuellen Referenzsortierung korrigiert
- Regionalblock jetzt: NDR, WDR, MDR, RBB, BR, SWR, SR, HR, Radio Bremen, ARD-alpha
- danach: Phoenix, tagesschau24, ZDFneo, ZDFinfo, ONE, WELT, n-tv, sixx
- anschließend: NITRO, Tele 5, Super RTL, KiKA, SPORT1, ProSieben MAXX, DMAX, Sat.1 Gold, RTLup, TLC

- alle 38 Senderlogos liegen jetzt als echte PNG-Binärdateien direkt unter `www/logos`
- der Docker-Build verarbeitet oder lädt keine Logos mehr; die fertigen Assets werden nur noch mit dem Add-on kopiert
- temporäre Base64-/Build-Hilfskonstruktion wird entfernt


- Buildpfad für Senderlogos komplett auf lokale Dateien umgestellt
- alle 38 Senderlogos liegen jetzt im Repository unter `data/logos_source`
- beim Docker-Build gibt es keine externen Logo-Downloads mehr
- dadurch können Netzwerk-, Wikimedia- oder GitHub-Raw-Fehler den Add-on-Build nicht mehr abbrechen

- Buildfehler behoben: keine zusätzliche Pillow/Alpine-Paketinstallation mehr nötig
- Logo-Build verwendet wieder ausschließlich Python-Standardbibliothek

- kuratierte lokale Senderlogo-Datenbank `data/logo_manifest.json` ergänzt
- für alle 38 Hauptsender feste Logo-Datei, Quelle und Quell-URL dokumentiert
- bevorzugt breite, gut lesbare Wortmarken; problematische Sender auf passendere Wikimedia-Varianten umgestellt
- Frontend verwendet die feste lokale Datei aus der Senderdatenbank

- Senderlogos füllen ihr Logo-Feld jetzt nahezu vollständig aus
- Normalisierung auf 260×64 px mit nur 2 px Sicherheitsrand
- jedes Logo wird proportional so groß skaliert, dass entweder Breite oder Höhe fast vollständig genutzt wird
- Theme-Erkennung robuster gemacht: Home-Assistant-Hintergrundfarbe wird zusätzlich per Helligkeit ausgewertet
- optionaler Theme-Modus `auto | dark | light` in den Add-on-Einstellungen
- Desktop-Spaltenzahl aus der Konfiguration wird wieder tatsächlich angewendet
- Änderungen nur auf `main`; keine neue Release-Version


## 0.5.8

- Senderlogos werden beim Add-on-Build jetzt automatisch auf sichtbare Pixel zugeschnitten
- transparente Leerflächen der Quellbilder werden entfernt
- alle Logos werden anschließend proportional auf eine einheitliche 220×64-Pixel-Fläche normalisiert
- dadurch erscheinen breite und hohe Logos deutlich gleichmäßiger und besser lesbar
- Das-Erste-Logo wieder auf die klar erkennbare Wikimedia-Variante umgestellt
- unter jedem Logo wird zusätzlich klein der Sendername angezeigt, damit der Sender auch bei ungewöhnlicher Wortmarke eindeutig erkennbar bleibt
- mobile Logo-Darstellung ebenfalls neu skaliert
- Pillow wird ausschließlich während des Builds verwendet und anschließend wieder aus dem Image entfernt


## 0.5.7

- Oberfläche übernimmt jetzt nach Möglichkeit die aktiven Home-Assistant-Theme-Farben direkt aus dem Ingress-Elternelement
- Hintergrund, Karten, Primär-/Sekundärtext, Trennlinien sowie Primär- und Akzentfarbe werden synchronisiert
- Theme-Wechsel in Home Assistant werden während der Laufzeit automatisch erkannt
- falls das Ingress-Elternelement nicht lesbar ist, greift automatisch `prefers-color-scheme` als Dark-/Light-Fallback
- laufende Sendung und Hover-Zustände werden aus der Home-Assistant-Primärfarbe abgeleitet
- kein fest erzwungener weißer Hintergrund mehr


## 0.5.6

- die letzten fünf Logo-Ausnahmen gezielt auf besser passende Wikimedia-PNGs umgestellt
- ARD-alpha: klar lesbare aktuelle HD-Variante
- RTLup: eindeutiges RTLup-Logo, damit es nicht wie ein doppeltes RTL wirkt
- ProSieben MAXX: breite, gut lesbare Wortmarke
- Sat.1 Gold: aktuelle Gold-Variante
- WELT: kontrastreiche WELT-TV-PNG
- damit haben jetzt alle 38 Hauptsender eine bewusst ausgewählte Logoquelle
- Logos bleiben fest im Add-on-Paket gebündelt und werden zur Laufzeit nicht aus dem Internet geladen


## 0.5.5

- Senderlogos systematisch auf einen einheitlich vorbereiteten Logo-Satz umgestellt
- 33 der 38 Hauptsender verwenden jetzt die auf 236×236 px mit transparentem Hintergrund normalisierten PNGs aus `cytec/tvlogos`
- diese Logos stammen dort aus Wikipedia/Wikimedia und sind bereits für gleichmäßige TV-/EPG-Darstellung zentriert
- ARD-alpha, RTLup, ProSieben MAXX, Sat.1 Gold und WELT bleiben vorerst auf dem bisherigen aktuellen Logo-Satz, weil im normalisierten Satz keine passende aktuelle Variante vorhanden ist
- Logoquelle wird pro Sender in der Senderdatenbank dokumentiert
- alle Bilder werden weiterhin beim Add-on-Build fest in das Paket übernommen; zur Laufzeit gibt es keine Logo-Downloads


## 0.5.4

- WDR, NDR, SWR, SR Fernsehen und Radio Bremen TV auf besser erkennbare HD-Logo-Varianten umgestellt
- behebt sehr kleine, veraltete oder nur teilweise sichtbare Regional-Senderlogos
- Logos bleiben weiterhin fest im Add-on-Paket gebündelt und werden nicht zur Laufzeit geladen


## 0.5.3

- Das-Erste-Logo auf die offizielle, sichtbare Wikimedia-PNG-Variante umgestellt
- behebt den leeren Senderkopf bei Das Erste
- Logo wird weiterhin beim Add-on-Build fest ins Paket übernommen; zur Laufzeit kein Internetabruf


## 0.5.2

- Senderlogos werden jetzt beim Add-on-Build einmalig heruntergeladen und fest in das Add-on-Paket übernommen
- kein Logo-Download mehr beim Start oder beim Öffnen der Oberfläche
- keine Logo-Abhängigkeit mehr von Browser, Referrer oder Laufzeit-Netzwerkzugriff
- Oberfläche lädt die Logos statisch aus `/www/logos/<sender>.png`
- der Build schlägt bewusst fehl, falls eines der vorgesehenen Senderlogos nicht verfügbar ist; damit wird kein Release mit unvollständigen Logos erzeugt


## 0.5.1

- alle Senderlogos werden beim Start in den Add-on-Datenspeicher heruntergeladen und lokal gecacht
- Oberfläche lädt Logos nur noch über das eigene Ingress-Backend statt direkt von GitHub
- behebt fehlende Logos durch externe Browser-/Referrer-/CORS-Probleme
- Logo-Dateien werden als PNG validiert und bei Bedarf automatisch nachgeladen
- Startlog zeigt jetzt exakt, wie viele Senderlogos lokal verfügbar sind
- RTLup bleibt als eigener Sender hinterlegt; Senderliste enthält keine doppelte RTL-ID


## 0.5.0

- Hauptsendergruppe von 20 auf 38 Sender erweitert
- ergänzt: ZDFneo, ZDFinfo, ONE, Phoenix, tagesschau24, KiKA, ARD-alpha
- ergänzt: RTLup, NITRO, Super RTL, ProSieben MAXX, Sat.1 Gold, sixx
- ergänzt: DMAX, TLC, WELT, n-tv und SPORT1
- für alle neuen Sender feste Logos und XMLTV-Aliase hinterlegt
- EPGShare DE1 ist jetzt direkt die Primärquelle, da der bisherige GitHub-Feed seit 2021 veraltet ist
- bestehende Nutzer mit der alten eingebauten Feed-URL werden automatisch auf EPGShare migriert


## 0.4.3

- vollständigen deutschen Senderlogo-Satz aus dem gepflegten tv-logo/tv-logos-Projekt verwendet
- Das-Erste-Logo auf die korrekte Datei `das-erste-de.png` umgestellt
- fehlendes RTLZWEI-Logo ergänzt
- alle 20 Hauptsender haben jetzt eine feste Logo-URL
- einheitliche Logo-Fläche von 132 × 46 px mit `object-fit: contain`
- Logos werden direkt geladen; Text-Fallback bleibt bei Ladefehlern erhalten


## 0.4.2

- Logo-Mapping für Das Erste korrigiert
- Senderlogos größenmäßig vereinheitlicht
- robuste Text-Fallbacks ergänzt, falls ein externes Logo nicht geladen werden kann
- kleine Abstands- und Höhenkorrekturen anhand des aktuellen Screenshots


## 0.4.1

- eigene Branding-Kopfzeile entfernt
- Navigation beginnt jetzt direkt mit JETZT / 20:15 / 22:00 / ANDERE ZEIT
- feste Senderlogos für alle 20 Hauptsender ergänzt
- Logos werden unabhängig vom jeweiligen EPG-Feed konsistent angezeigt
- Logo-Größen und Senderkopf stärker an die klassische TV-Programmansicht angeglichen
- Merkliste kompakt in die Sendergruppen-Zeile verschoben


## 0.4.0

- Oberfläche grundlegend als klassische TV-Zeitschrift neu aufgebaut
- zentrale Schnellwahl JETZT / 20:15 / 22:00 / ANDERE ZEIT
- horizontale Tagesleiste für heute plus sieben Folgetage
- Senderkarten mit Logo-Spalte, Uhrzeit, Titel, Genre und Pfeil zur Detailansicht
- laufende Sendung mit JETZT-Markierung, Restzeit und Fortschrittsbalken
- mobile Darstellung als kompakte Sender-/Programmzeilen
- Sendungen können lokal im Browser gemerkt und wieder entfernt werden
- eigene TV-Guide-Marke statt Übernahme geschützter fremder Markenassets
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
