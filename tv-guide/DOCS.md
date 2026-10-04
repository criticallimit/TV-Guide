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

TV Guide lädt echte XMLTV-Daten aus mehreren fest eingebauten Deutschland-Quellen. Priorität ist eine möglichst breite Sender- und Programmdatenabdeckung, nicht eine möglichst lange Vorschau.

Aktuell werden automatisch zusammengeführt:

1. Open-EPG Deutschland: `https://www.open-epg.com/files/germany.xml.gz`
2. EPGShare01 DE1: `https://epgshare01.online/epgshare01/epg_ripper_DE1.xml.gz`
3. epg.pw Deutschland: `https://epg.pw/xmltv/epg_DE.xml.gz`

Die Quellen werden unabhängig geladen und ausgewertet. Programme desselben Senders werden zusammengeführt, Dubletten entfernt und bei konkurrierenden Einträgen die vollständigeren Metadaten bevorzugt. Fällt eine einzelne Quelle aus, werden die übrigen Quellen trotzdem verwendet.

Bei den eingebauten Quellen wird nicht nur der HTTP-Download geprüft. TV Guide verwirft eine Quelle auch dann, wenn sie zu wenig Sender mit Programmdaten liefert, zu wenige der 50 Hauptsender abdeckt oder nicht mindestens sechs Stunden in die Zukunft reicht.

Die EPG-Quellen sind bewusst keine Benutzereinstellung mehr. Die Quellenverwaltung ist Teil des Add-ons, damit Updates die beste verfügbare Kombination automatisch anpassen können.

Der heruntergeladene XMLTV-Feed und zusätzlich die bereits ausgewerteten Programmdaten werden persistent in `/data` zwischengespeichert. Dadurch kann die Oberfläche nach einem Add-on-Neustart sofort die zuletzt gültigen Daten anzeigen, während im Hintergrund aktualisiert wird.

## Konfiguration

- **Standardansicht**: Jetzt, 20:15 oder 22:00
- **Spalten am Desktop**: 3 bis 6
- **Angezeigte Sender**: 0 bis 500; `0` zeigt alle Sender der gewählten Liste
- **Darstellung**: automatisch, dunkel oder hell
- **Aktualisierungsintervall**: 30 bis 1440 Minuten
- **Empfänger der Erinnerungen**: Home Assistant oder ein verbundenes Mobilgerät der Home-Assistant-Mobile-App

Standard für Erinnerungen ist **Home Assistant**. Zusätzlich werden verbundene Geräte der Home-Assistant-Mobile-App automatisch als auswählbare Ziele angeboten.

## Sender

Die Hauptsendergruppe umfasst 50 Sender in der festgelegten HÖRZU-Referenzreihenfolge. Die Standardsortierung bleibt fest im Add-on hinterlegt.

Benutzer können die Sender in der Oberfläche selbst sortieren oder ausblenden. Die persönliche Konfiguration wird persistent in `/data/tv_guide_channel_order.json` gespeichert und bleibt bei Add-on-Updates erhalten. Über **Standardsortierung** lässt sich die Ausgangsreihenfolge jederzeit wiederherstellen.

## Erinnerungen

Eine Sendung kann unabhängig von einer Erinnerung gemerkt werden. Bei gemerkten zukünftigen Sendungen lässt sich **Erinnern** per Kontrollkästchen aktivieren; erst dann erscheint die Auswahl für 5, 10, 15 oder 30 Minuten Vorlauf.

Erinnerungen werden persistent in `/data/tv_guide_reminders.json` gespeichert und funktionieren deshalb auch nach einem Add-on-Neustart weiter. Ein Hintergrundprozess prüft regelmäßig, ob eine Erinnerung fällig ist, und ruft dann den konfigurierten Home-Assistant-Benachrichtigungsdienst auf.

## Radio Bremen TV

Falls der XMLTV-Feed Radio Bremen TV nicht enthält, versucht TV Guide den Sender zusätzlich über die offizielle Programmübersicht der ARD Mediathek zu ergänzen.


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
