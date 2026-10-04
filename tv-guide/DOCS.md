# TV Guide

Nach der Installation kann **TV Guide** über den Home-Assistant-Ingress geöffnet werden.


## Senderkatalog und eigene Senderliste

Der TV Guide liest nicht nur die vorkonfigurierten Hauptsender ein. Jeder Sender, der im aktiven XMLTV-Feed als `<channel>` enthalten ist und Programmdaten liefert, wird in den internen Senderkatalog übernommen.

- Die bisherigen Hauptsender bleiben die Standardauswahl nach einer Neuinstallation oder nach „Zurücksetzen“.
- Weitere Sender aus dem EPG-Feed werden im Senderkatalog zusätzlich angeboten.
- Die Senderverwaltung kann diese Sender aktivieren, deaktivieren und in eine eigene Reihenfolge bringen.
- Die gespeicherte Auswahl verwendet stabile interne IDs und bleibt über EPG-Aktualisierungen und Add-on-Neustarts erhalten.
- Alle 50 Hauptsender besitzen eine feste Logo-Fallbackquelle; bestehende gebündelte Logos bleiben erhalten.
- Jedes Senderlogo wird über dieselbe Normalisierung auf eine feste 260×64-Fläche gebracht und persistent in `/data/tv_guide_logos` zwischengespeichert.
- Für helle und dunkle Darstellung werden getrennte normalisierte SVG-Varianten erzeugt. Die Dark-Variante behält die Markenfarben und ergänzt eine dezente helle Kontur für dunkle Logoanteile.
- Auch zusätzliche XMLTV-Sender in „Meine Sender“ verwenden diese Pipeline. Feed-Logos werden lokal gecacht, sodass die eigene Senderliste dieselbe Logo-Größe und Ausrichtung verwendet.

Die Anzahl der auswählbaren Sender ist nicht auf die 50 Hauptsender beschränkt.

## Programmdaten

TV Guide bevorzugt bestätigte Programmdaten des jeweiligen Senders. Öffentliche Senderseiten mit ausdrücklich datierten Sendungen stehen an erster Stelle, der sendereigene Videotext an zweiter Stelle. Die eingebauten XMLTV- und sekundären Webquellen ergänzen nur unbesetzte Zeiträume.

Aktuell werden automatisch zusammengeführt:

1. Open-EPG Deutschland: `https://www.open-epg.com/files/germany.xml.gz`
2. EPGShare01 DE1: `https://epgshare01.online/epgshare01/epg_ripper_DE1.xml.gz`

Der zuvor eingebaute epg.pw-Feed ist wegen nachgewiesener systematischer Abweichungen aus der aktiven Quellenliste entfernt.

Die Quellen werden unabhängig geladen und ausgewertet. Programme desselben Senders werden zusammengeführt und Dubletten entfernt. Bei Konflikten gewinnt die offizielle Senderquelle unabhängig von der numerischen Quellenpriorität. Auch wenn sämtliche XMLTV-Downloads ausfallen, werden die offiziellen Senderquellen abgefragt.

Das Zusammenführen toleriert kleine Zeitabweichungen zwischen Quellen (derzeit bis zu vier Minuten), wenn der Sendungstitel übereinstimmt oder eindeutig zueinander passt. Offizielle Start- und Endzeiten, Titel und Beschreibungen werden dabei nicht durch Angaben anderer Quellen überschrieben oder ergänzt. Metadaten werden nur zwischen passenden Sendungen derselben Vertrauensstufe ergänzt.

Für jeden Refresh werden Qualitätsmetriken gespeichert: Anzahl gelieferter Sender, Hauptsender, Programme, Reichweite der Quelle sowie Fehlerstatus. Zusätzlich wird für jeden der 50 Hauptsender der Live-Status seines offiziellen Providers protokolliert (`ok`, `no_data`, `error` oder `no_verified_provider`). Diese Daten stehen über `/api/status` zur Diagnose bereit.

Bei den eingebauten Quellen wird nicht nur der HTTP-Download geprüft. Im Multi-Source-Modell bleiben auch kleine Teilquellen erhalten, wenn sie aktuelle verwertbare Programmdaten liefern; sie können Lücken größerer Feeds schließen. Verworfen werden nur Quellen ohne brauchbare Programme oder Quellen, deren Daten nicht mehr ausreichend aktuell sind.

Die EPG-Quellen sind bewusst keine Benutzereinstellung mehr. Die Quellenverwaltung ist Teil des Add-ons, damit Updates die beste verfügbare Kombination automatisch anpassen können.

Im Guide werden fehlende Daten unterschieden: keine Programmdaten für den Sender, abgelaufene Daten, früher endende Daten oder vorübergehend nicht erreichbare Quellen. Dadurch ist ein fehlender Eintrag nicht mehr pauschal nur „Keine EPG-Daten“.


Die senderbezogene Provider-Schicht liest ausdrücklich datierte Sendungseinträge aus ARD-, SR- und RTL-Seiten aus. RTL-Daten werden zusätzlich auf den genauen Sender geprüft; Daten anderer Sender auf derselben Seite werden nicht übernommen. Reine Navigationszeiten und Seiten ohne nachweisbares Programmdatum werden nicht als Sendungen verwendet. `/api/guide` enthält je Sendung die Quelle und deren Herkunftsart.

Als zusätzliche offizielle Quelle werden dort, wo sie stabil im Web erreichbar sind, auch Videotext-/Teletext-Programmseiten ausgewertet. Aktuell sind ARD Text, ZDFtext (ZDF, ZDFneo, ZDFinfo, 3sat), WDR Text und die direkt erreichbaren NDR-Text-Seiten eingebunden. Diese Daten werden nicht separat angezeigt, sondern mit den übrigen offiziellen und XMLTV-Daten desselben Senders zusammengeführt.

Für **46 der 50 Hauptsender** sind offizielle Webseiten hinterlegt. Das bedeutet nicht, dass jede Seite jederzeit auslesbare Programmdaten liefert: Manche Angebote laden die Daten erst im Browser oder beschränken den Schnittstellenzugang. Fehlende oder nicht verifizierbare Angaben werden verworfen. Für **Euronews, HGTV, Nickelodeon und Comedy Central** ist derzeit kein stabiler öffentlich auslesbarer offizieller EPG-Endpunkt belegt. Fremdquellen bleiben für solche Datenlücken ein Ersatz, ohne bestätigte Senderangaben zu verdrängen.

Die Programmdaten werden persistent in `/data` zwischengespeichert. Cache-Schema 8 speichert die Quellenherkunft und bereinigte Videotext-Titel. Die älteren Schemas 5 bis 7 werden vollständig neu aufgebaut; ein frischer Dateizeitstempel allein gilt nicht als Beleg für aktuelle Sendungsdaten.

## Konfiguration

- **Standardansicht**: Jetzt, 20:15 oder 22:00
- **Spalten am Desktop**: 3 bis 6
- **Angezeigte Sender**: 0 bis 500; `0` zeigt alle Sender der gewählten Liste
- **Darstellung**: automatisch, dunkel oder hell
- **Aktualisierungsintervall**: 30 bis 1440 Minuten
- **Empfänger der Erinnerungen**: Home Assistant oder ein verbundenes Mobilgerät der Home-Assistant-Mobile-App

Standard für Erinnerungen ist **Home Assistant**. Zusätzlich werden verbundene Geräte der Home-Assistant-Mobile-App automatisch als auswählbare Ziele angeboten.

## Sender

Die Hauptsendergruppe umfasst 50 Sender in der festgelegten Senderreihenfolge. Die Standardsortierung bleibt fest im Add-on hinterlegt.

Benutzer können die Sender in der Oberfläche selbst sortieren oder ausblenden. Die persönliche Konfiguration wird persistent in `/data/tv_guide_channel_order.json` gespeichert und bleibt bei Add-on-Updates erhalten. Über **Standardsortierung** lässt sich die Ausgangsreihenfolge jederzeit wiederherstellen.

## Erinnerungen

Eine Sendung kann unabhängig von einer Erinnerung gemerkt werden. Bei gemerkten zukünftigen Sendungen lässt sich **Erinnern** per Kontrollkästchen aktivieren; erst dann erscheint die Auswahl für 5, 10, 15 oder 30 Minuten Vorlauf.

Erinnerungen werden persistent in `/data/tv_guide_reminders.json` gespeichert und funktionieren deshalb auch nach einem Add-on-Neustart weiter. Ein Hintergrundprozess prüft regelmäßig, ob eine Erinnerung fällig ist, und ruft dann den konfigurierten Home-Assistant-Benachrichtigungsdienst auf.

## Lovelace-Karte

TV Guide liefert eine eigene Lovelace-Karte mit. Beim Start werden die benötigten Kartendateien für Home Assistant bereitgestellt.

Einmalige Einrichtung:

1. **Einstellungen → Dashboards** öffnen.
2. Oben rechts **Ressourcen** öffnen.
3. **Ressource hinzufügen** wählen.
4. URL: `/local/tv-guide-card-loader.js`
5. Typ: **JavaScript-Modul**
6. Home Assistant im Browser neu laden.

Das Zahnrad-Menü zeigt dabei den Status **Bereit**, **Ressource fehlt** oder **Noch nicht bereit** und bietet Schaltflächen zum Kopieren der Ressourcen-URL, zum Öffnen der Ressourcen-Seite und zum erneuten Prüfen.

Danach steht **TV Guide** im normalen Dialog **Karte hinzufügen** zur Auswahl.

Die Karte zeigt die aktuell konfigurierte Senderauswahl und bietet die Schnellansichten **Jetzt**, **20:15** und **22:00**. Änderungen an Senderreihenfolge oder ausgeblendeten Sendern werden automatisch übernommen.

Falls auf der Installation bisher noch nie `/local` verwendet wurde, kann nach dem ersten Start des Add-ons einmalig ein Neustart von Home Assistant nötig sein.
