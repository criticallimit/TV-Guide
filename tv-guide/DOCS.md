# TV Guide

Nach der Installation kann **TV Guide** über den Home-Assistant-Ingress geöffnet werden.

## Programmdaten

TV Guide lädt echte XMLTV-Daten. Als Standardquelle wird der kostenlose Deutschland-Feed von EPGShare01 verwendet:

`https://epgshare01.online/epgshare01/epg_ripper_DE1.xml.gz`

Veraltete Feeds werden automatisch erkannt, wenn ihre Programmdaten nicht mehr bis zur aktuellen Zeit reichen.

Der heruntergeladene XMLTV-Feed und zusätzlich die bereits ausgewerteten Programmdaten werden persistent in `/data` zwischengespeichert. Dadurch kann die Oberfläche nach einem Add-on-Neustart sofort die zuletzt gültigen Daten anzeigen, während im Hintergrund aktualisiert wird.

## Konfiguration

- **Standardansicht**: Jetzt, 20:15 oder 22:00
- **Spalten am Desktop**: 3 bis 6
- **Darstellung**: automatisch, dunkel oder hell
- **EPG-URL**: URL zu einer XMLTV- oder XMLTV-GZIP-Datei
- **Aktualisierungsintervall**: 30 bis 1440 Minuten
- **Benachrichtigungsdienst**: Home-Assistant-Dienst für TV-Erinnerungen

Standard für Erinnerungen ist:

`persistent_notification.create`

Für Push-Benachrichtigungen auf ein Smartphone kann stattdessen ein vorhandener Home-Assistant-Dienst wie `notify.mobile_app_mein_handy` eingetragen werden.

## Sender

Die Hauptsendergruppe umfasst 38 deutsche Sender. Die Standardsortierung bleibt fest im Add-on hinterlegt.

Benutzer können die Sender in der Oberfläche selbst sortieren oder ausblenden. Die persönliche Konfiguration wird persistent in `/data/tv_guide_channel_order.json` gespeichert und bleibt bei Add-on-Updates erhalten. Über **Standardsortierung** lässt sich die Ausgangsreihenfolge jederzeit wiederherstellen.

## Erinnerungen

Bei zukünftigen Sendungen kann direkt in der Detailansicht eine Erinnerung gesetzt werden. Unterstützt werden 5, 10, 15 oder 30 Minuten Vorlauf.

Erinnerungen werden persistent in `/data/tv_guide_reminders.json` gespeichert und funktionieren deshalb auch nach einem Add-on-Neustart weiter. Ein Hintergrundprozess prüft regelmäßig, ob eine Erinnerung fällig ist, und ruft dann den konfigurierten Home-Assistant-Benachrichtigungsdienst auf.

## Radio Bremen TV

Falls der XMLTV-Feed Radio Bremen TV nicht enthält, versucht TV Guide den Sender zusätzlich über die offizielle Programmübersicht der ARD Mediathek zu ergänzen.
