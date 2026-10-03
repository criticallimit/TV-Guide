# TV Guide for Home Assistant

TV Guide bringt eine übersichtliche Fernsehprogramm-Ansicht direkt in Home Assistant. Das aktuelle Programm, die wichtigsten Sendezeiten und weitere Tage lassen sich schnell durchsuchen. Die Senderliste kann persönlich sortiert oder reduziert werden, Sendungen lassen sich merken und auf Wunsch mit einer Erinnerung versehen.

## Installation

1. In Home Assistant den **App-/Add-on-Store** öffnen.
2. Unter **Repositories** `https://github.com/criticallimit/TV-Guide` hinzufügen.
3. **TV Guide** installieren und starten.
4. Optional **In Seitenleiste anzeigen** aktivieren.

## Nutzung

TV Guide kann direkt über die Home-Assistant-Seitenleiste geöffnet werden. Dort steht die Programmübersicht wie eine eigene Home-Assistant-Seite zur Verfügung.

Alternativ kann TV Guide auch in ein eigenes Lovelace-Dashboard eingebunden werden:

1. Das gewünschte Dashboard öffnen und **Bearbeiten** wählen.
2. **Karte hinzufügen** und eine **Webseite/Webpage-Karte** auswählen.
3. TV Guide einmal über Home Assistant öffnen und die dort verwendete Ingress-Adresse als URL der Karte verwenden.
4. Höhe der Karte nach Wunsch anpassen.

So kann TV Guide zum Beispiel zusammen mit Fernbedienung, Media Playern oder weiteren Wohnzimmer-Funktionen auf einer gemeinsamen Dashboard-Seite angezeigt werden.

## Funktionen

TV Guide zeigt das Fernsehprogramm in einer kompakten, für Desktop und Mobilgeräte geeigneten Ansicht. Sender können individuell sortiert oder ausgeblendet werden. Gemerkte Sendungen stehen innerhalb desselben Home-Assistant-Systems geräteübergreifend zur Verfügung und können mit einer optionalen Erinnerung versehen werden.

Die Programmdaten werden automatisch aktualisiert. Die Standardsortierung kann jederzeit wiederhergestellt werden.
