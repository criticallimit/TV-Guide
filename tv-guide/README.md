# TV Guide für Home Assistant – dein Fernsehprogramm

TV Guide ist ein Home-Assistant-Add-on für dein Fernsehprogramm: Sieh, was gerade im TV läuft, plane deinen Fernsehabend und lass dich an deine Lieblingssendungen erinnern. Die Programmübersicht passt auf große Bildschirme ebenso wie auf das Handy und übernimmt auf Wunsch die helle oder dunkle Darstellung von Home Assistant.

[Projektseite](https://criticallimit.github.io/TV-Guide/) · [In Home Assistant hinzufügen](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fcriticallimit%2FTV-Guide)

## Das bietet TV Guide

- **Schnell zum richtigen Programm:** Jetzt, 20:15 Uhr, 22:00 Uhr oder ein anderer Tag und eine frei gewählte Uhrzeit.
- **Deine Sender, deine Reihenfolge:** 50 vorbereitete Hauptsender und weitere Sender, soweit Programmdaten verfügbar sind. Stelle unter „Meine Sender“ deine persönliche Auswahl zusammen.
- **Mehr zur Sendung:** Tippe auf einen Eintrag, um die verfügbaren Informationen zu öffnen.
- **Merkliste und Erinnerungen:** Merke Sendungen und aktiviere bei zukünftigen Sendungen bei Bedarf eine Erinnerung 5, 10, 15 oder 30 Minuten vorher.
- **Auch beim Scrollen erreichbar:** Die Kopfzeile mit Uhrzeiten, Senderlisten und Einstellungen bleibt oben stehen.
- **Gut lesbar in Hell und Dunkel:** Passende Senderlogos und eine kompakte Programmübersicht.

## Installation

Du benötigst eine Home-Assistant-Installation mit App-/Add-on-Store, beispielsweise Home Assistant OS.

1. Öffne **Einstellungen → Apps** beziehungsweise **Add-ons** und den Store.
2. Öffne das Menü **Repositories** und füge diese Adresse hinzu:
   `https://github.com/criticallimit/TV-Guide`
3. Installiere **TV Guide** und starte die App.
4. Aktiviere bei Bedarf **In Seitenleiste anzeigen** und öffne **TV Programm**.

Beim ersten Start werden die Programmdaten geladen. Die Übersicht öffnet sich bereits währenddessen; bis alle verfügbaren Sender gefüllt sind, kann es einige Minuten dauern.

## So nutzt du die Übersicht

Wähle oben **Jetzt**, **20:15** oder **22:00**. Mit **Andere Zeiten** kannst du einen verfügbaren Tag und die gewünschte Uhrzeit auswählen. Der Fortschrittsbalken zeigt bei einer laufenden Sendung, wie weit sie bereits fortgeschritten ist.

**Hauptsender** zeigt die vorbereitete Senderliste. Unter **☰ Sender** legst du fest, welche Sender unter **Meine Sender** erscheinen und in welcher Reihenfolge. Mit **Standardsortierung** stellst du die Ausgangsauswahl wieder her.

Tippe auf eine Sendung und wähle **Merken**. Deine Merkliste findest du über **★ Gemerkt**. Für eine gemerkte zukünftige Sendung kannst du zusätzlich **Erinnern** aktivieren und den gewünschten Vorlauf wählen. Im Zahnrad-Menü stellst du ein, ob die Nachricht in Home Assistant oder auf einem verbundenen Handy ankommen soll. Dort kannst du die Benachrichtigung auch testen.

Die Senderauswahl und gespeicherten Sendungen stehen auf deinen Geräten innerhalb derselben Home-Assistant-Installation zur Verfügung. Sie bleiben auch bei einem Neustart oder Update erhalten.

## Auf deinem Dashboard

Am einfachsten nutzt du TV Guide über die Seitenleiste. Für dein Dashboard gibt es zusätzlich eine **TV Guide-Karte**.

1. Starte TV Guide und öffne das **Zahnrad-Menü**. Dort findest du die Hilfe zur Dashboard-Karte.
2. Füge unter **Einstellungen → Dashboards → Ressourcen** einmal die Adresse `/local/tv-guide-card-loader.js` mit dem Typ **JavaScript-Modul** hinzu. Falls „Ressourcen“ fehlt, aktiviere im Benutzerprofil den erweiterten Modus.
3. Lade Home Assistant im Browser neu.
4. Bearbeite dein Dashboard und wähle **Karte hinzufügen → TV Guide**.

Wenn du erstmals Dashboard-Ressourcen verwendest und die Karte noch nicht erscheint, starte Home Assistant einmal neu. Das Zahnrad-Menü hilft dir, den Einrichtungsstatus zu prüfen.

## Einstellungen

Im **Zahnrad-Menü** kannst du die Startansicht, die Anzahl der Sender pro Reihe, die angezeigte Senderanzahl, die Darstellung und das Aktualisierungsintervall ändern. Bei der Senderanzahl bedeutet **0**, dass alle Sender der ausgewählten Liste angezeigt werden.

## Wenn etwas fehlt

**Ein Sender hat kein Programm:** Die Verfügbarkeit hängt von den öffentlich erreichbaren Quellen ab. TV Guide bevorzugt bestätigte Angaben der Sender und ergänzt Lücken durch weitere Quellen. Nicht für jeden Sender und jeden Tag sind Daten verfügbar; Programmänderungen können verzögert ankommen.

**Die Übersicht ist nach einem Update zunächst leer:** Frühere Programmdaten werden bei Bedarf neu geladen. Lass die App einige Minuten laufen und öffne die Übersicht erneut.

**Eine Erinnerung kommt nicht an:** Prüfe im Zahnrad-Menü das Benachrichtigungsziel und sende eine Testnachricht. Für Handy-Erinnerungen muss das Gerät mit der Home-Assistant-App verbunden sein. TV Guide und Home Assistant müssen zum Erinnerungszeitpunkt laufen.

## Aktualisieren und Hilfe

Updates installierst du im Home-Assistant-App-/Add-on-Store. Deine gespeicherten Einstellungen, Senderlisten und Sendungen bleiben erhalten.

Bei Problemen kannst du [auf GitHub einen Fehler melden](https://github.com/criticallimit/TV-Guide/issues). Beschreibe bitte, was passiert, und nenne den betroffenen Sender, Tag und die Uhrzeit.
