# TV Guide for Home Assistant

TV Guide bringt eine übersichtliche Fernsehprogramm-Ansicht direkt in Home Assistant. Das aktuelle Programm, die wichtigsten Sendezeiten und weitere Tage lassen sich schnell durchsuchen. Die Senderliste kann persönlich sortiert oder reduziert werden, Sendungen lassen sich merken und auf Wunsch mit einer Erinnerung versehen.

## Installation

1. In Home Assistant den **App-/Add-on-Store** öffnen.
2. Unter **Repositories** `https://github.com/criticallimit/TV-Guide` hinzufügen.
3. **TV Guide** installieren und starten.
4. Optional **In Seitenleiste anzeigen** aktivieren.

## Nutzung

TV Guide kann direkt über die Home-Assistant-Seitenleiste geöffnet werden. Dort steht die Programmübersicht wie eine eigene Home-Assistant-Seite zur Verfügung.

Alternativ kann TV Guide als eigene **TV Guide-Karte** in einem Lovelace-Dashboard verwendet werden.

Nach dem ersten Start des Add-ons einmal unter **Einstellungen → Dashboards → Ressourcen** die Ressource `/local/tv-guide-card.js?v=0.5.9` als **JavaScript-Modul** hinzufügen. Danach Home Assistant neu laden. Anschließend erscheint **TV Guide** ganz normal im Dialog **Karte hinzufügen**, wie andere auswählbare Karten auch.

So kann die Programmübersicht zusammen mit Fernbedienung, Media Playern oder weiteren Wohnzimmer-Funktionen auf einer gemeinsamen Dashboard-Seite angezeigt werden.

## Funktionen

TV Guide zeigt das Fernsehprogramm in einer kompakten, für Desktop und Mobilgeräte geeigneten Ansicht. Sender können individuell sortiert oder ausgeblendet werden. Gemerkte Sendungen stehen innerhalb desselben Home-Assistant-Systems geräteübergreifend zur Verfügung und können mit einer optionalen Erinnerung versehen werden.

Die Programmdaten werden automatisch aktualisiert. Die Standardsortierung kann jederzeit wiederhergestellt werden.
