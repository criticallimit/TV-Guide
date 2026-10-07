# TV Guide voor Home Assistant


Het Verenigd Koninkrijk wordt ook ondersteund met een voorbereide lijst met hoofdzenders.
Bekijk wat er nu op tv is, plan je avond en bewaar programma’s met een herinnering. De gids werkt op grote schermen en mobiele apparaten, in een lichte of donkere weergave.

[Dansk](https://criticallimit.github.io/TV-Guide/manuals/da.html) · [Deutsch](https://criticallimit.github.io/TV-Guide/manuals/de.html) · [English](https://criticallimit.github.io/TV-Guide/manuals/en.html) · [Español](https://criticallimit.github.io/TV-Guide/manuals/es.html) · [Nederlands](https://criticallimit.github.io/TV-Guide/manuals/nl.html) · [Français](https://criticallimit.github.io/TV-Guide/manuals/fr.html) · [Italiano](https://criticallimit.github.io/TV-Guide/manuals/it.html) · [Norsk](https://criticallimit.github.io/TV-Guide/manuals/nb.html) · [Svenska](https://criticallimit.github.io/TV-Guide/manuals/sv.html)

## Installeren

Je hebt Home Assistant met de app-/add-onwinkel nodig, bijvoorbeeld Home Assistant OS.

1. Open **Instellingen → Apps** (of **Add-ons**) en de winkel.
2. Voeg bij **Repositories** `https://github.com/criticallimit/TV-Guide` toe.
3. Installeer en start **TV Guide** en activeer de weergave in de zijbalk.
4. Open **TV Guide**. De eerste programmagegevens kunnen enkele minuten nodig hebben.

## Land en taal

Open de instellingen via het tandwiel. Onder **Land en taal** kies je Duitsland, Oostenrijk, Zwitserland, Nederland, België, Denemarken, Noorwegen, Frankrijk of Zweden. Elk land heeft een eigen hoofdzenderlijst en extra zenders wanneer gegevens beschikbaar zijn. Zwitserland bevat de drie taalregio’s; België bevat Nederlandse en Franse zenders.

**Automatisch · Home Assistant** volgt eerst je profieltaal en daarna de installatie-instellingen. Zonder beschikbare taal kiest de gids Deens voor Denemarken, Duits voor Duitsland en Oostenrijk, Nederlands voor Nederland, Noors voor Noorwegen, Frans voor Frankrijk en Zweeds voor Zweden. Voor meertalige landen wordt de browsertaal gebruikt; Engels is de terugvaltaal. Deens, Duits, Engels, Nederlands, Frans, Italiaans, Noors en Zweeds zijn ook handmatig te kiezen. De taal staat los van het tv-land. Programmatitels en beschrijvingen behouden hun oorspronkelijke taal.

## Je programma en zenders

Kies **Nu**, **18:00**, **20:15**, **22:00** of **Andere tijden**. Klik op een programma voor meer informatie. **Hoofdzenders** toont de voorbereide lijst. Via **☰ Zenders** kies en sorteer je **Mijn zenders**. Je persoonlijke keuze wordt per land bewaard; **Standaardvolgorde** herstelt de beginlijst.

De instellingen zijn gegroepeerd in **Land en taal**, **Weergave** en **Herinneringen**. Stel onder Weergave de startweergave, het uiterlijk en het aantal zenders in. **0** toont de volledige gekozen lijst. Het verversingsinterval staat onder **Geavanceerd**. Klik op **Opslaan** om wijzigingen toe te passen.

## Programma’s bewaren en herinneringen

Open een programma en kies **Bewaren**. Je vindt het terug bij **★ Bewaard**. Voor toekomstige bewaarde programma’s kun je **Herinneren** inschakelen, 5, 10, 15 of 30 minuten vooraf.

Kies in de instellingen onder **Herinneringen** Home Assistant of een verbonden mobiel apparaat en klik op **Melding testen**. Home Assistant en TV Guide moeten actief zijn wanneer de herinnering wordt verstuurd. Een herinnering behoudt de taal waarin je deze hebt gemaakt.

## Op je dashboard

Open **Op je dashboard** in de instellingen. Voeg in Home Assistant onder **Instellingen → Dashboards → Bronnen** `/local/tv-guide-card-loader.js` toe als **JavaScript-module**. Schakel zo nodig geavanceerde modus in je profiel in om Bronnen te zien. Herlaad Home Assistant en voeg de TV Guide-kaart toe. Verschijnt de eerste kaart niet, herstart Home Assistant eenmaal.

## Als iets ontbreekt

Programma’s hangen af van openbare bronnen. Bevestigde omroepgegevens hebben voorrang; andere bronnen vullen ontbrekende gegevens aan. Nederland gebruikt momenteel een gecontroleerde openbare programmabron. Niet alle zenders of dagen zijn altijd beschikbaar. Wacht bij een leeg overzicht na een update of landwissel enkele minuten.

Werkt een herinnering niet, controleer dan de ontvanger en stuur een testmelding. Mobiele apparaten moeten verbonden zijn met de Home Assistant-app.

Updates installeer je via de winkel. Zenderlijsten en bewaarde programma’s blijven behouden. Wijzigingen op main kunnen vóór de volgende release verschijnen.

[Probleem melden](https://github.com/criticallimit/TV-Guide/issues): vermeld het land, de zender, datum en tijd.

Frankrijk bevat 24 nationale hoofdzenders. BFMTV is voorlopig niet beschikbaar.
