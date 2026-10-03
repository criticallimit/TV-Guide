# TV Guide for Home Assistant

Home-Assistant-App/Add-on mit Ingress-Oberfläche für eine klassische TV-Programmübersicht.

## Installation

1. Home Assistant öffnen.
2. Einstellungen → Apps/Add-ons → App-/Add-on-Store.
3. Repositories öffnen.
4. `https://github.com/criticallimit/TV-Guide` hinzufügen.
5. **TV Guide** installieren und starten.
6. Optional **In Seitenleiste anzeigen** aktivieren.

## Funktionen

- echte XMLTV/EPG-Programmdaten
- 38 vorkonfigurierte deutsche Hauptsender
- lokale, gebündelte Senderlogos
- Ansichten **Jetzt**, **20:15**, **22:00** und freie Zeitwahl
- responsive Desktop- und Mobilansicht
- Home-Assistant-Theme-Unterstützung
- persistenter EPG-Cache für schnellen Start
- eigene Senderreihenfolge und Sender ausblenden
- Standardsortierung jederzeit wiederherstellbar
- geräteübergreifende Merkliste
- optionale TV-Erinnerungen über Home-Assistant-Benachrichtigungsdienste
- frei konfigurierbare XMLTV-Quelle

## Standardquelle

Vorkonfiguriert ist der kostenlose Deutschland-Feed von EPGShare01:

`https://epgshare01.online/epgshare01/epg_ripper_DE1.xml.gz`

Die Quelle kann in den Add-on-Einstellungen ersetzt werden.

## Datenschutz und Betrieb

TV Guide benötigt keinen externen Benutzeraccount. Persönliche Senderreihenfolge, Merkliste, Erinnerungen und EPG-Cache werden im persistenten Add-on-Datenspeicher von Home Assistant abgelegt.
