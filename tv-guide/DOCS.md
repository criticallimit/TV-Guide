# TV Guide

Nach der Installation kann **TV Guide** über den Home-Assistant-Ingress geöffnet werden.

## Programmdaten

TV Guide lädt echte XMLTV-Daten. Als Standardquelle wird der kostenlose Deutschland-Feed von EPGShare01 verwendet:

`https://epg.pw/xmltv/epg_DE.xml.gz`\n\nDie bisherige epgshare01-DE1-Quelle bleibt als automatische Rückfallquelle erhalten, falls der Standardfeed nicht geladen oder verarbeitet werden kann.

Veraltete Feeds werden automatisch erkannt, wenn ihre Programmdaten nicht mehr bis zur aktuellen Zeit reichen.

Der heruntergeladene XMLTV-Feed und zusätzlich die bereits ausgewerteten Programmdaten werden persistent in `/data` zwischengespeichert. Dadurch kann die Oberfläche nach einem Add-on-Neustart sofort die zuletzt gültigen Daten anzeigen, während im Hintergrund aktualisiert wird.

## Konfiguration

- **Standardansicht**: Jetzt, 20:15 oder 22:00
- **Spalten am Desktop**: 3 bis 6
- **Angezeigte Sender**: 0 bis 38; `0` zeigt alle nicht ausgeblendeten Sender
- **Darstellung**: automatisch, dunkel oder hell
- **EPG-URL**: URL zu einer XMLTV- oder XMLTV-GZIP-Datei
- **Aktualisierungsintervall**: 30 bis 1440 Minuten
- **Empfänger der Erinnerungen**: Home Assistant oder ein verbundenes Mobilgerät der Home-Assistant-Mobile-App

Standard für Erinnerungen ist **Home Assistant**. Zusätzlich werden verbundene Geräte der Home-Assistant-Mobile-App automatisch als auswählbare Ziele angeboten.

## Sender

Die Hauptsendergruppe umfasst 38 deutsche Sender. Die Standardsortierung bleibt fest im Add-on hinterlegt.

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
