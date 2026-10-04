# TV Guide voor Home Assistant

Bekijk wat er nu op tv is, plan je avond en bewaar programma’s met een herinnering. De gids werkt op grote schermen en mobiele apparaten, in een lichte of donkere weergave.

## Installeren

Je hebt Home Assistant met de app-/add-onwinkel nodig, bijvoorbeeld Home Assistant OS.

1. Open **Instellingen → Apps** (of **Add-ons**) en de winkel.
2. Voeg bij **Repositories** `https://github.com/criticallimit/TV-Guide` toe.
3. Installeer en start **TV Guide** en activeer de weergave in de zijbalk.
4. Open **TV Guide**. De eerste programmagegevens kunnen enkele minuten nodig hebben.

## Land en taal

Open de instellingen via het tandwiel. Onder **Land en taal** kies je Duitsland, Oostenrijk, Zwitserland, Nederland, België of Noorwegen. Elk land heeft een eigen hoofdzenderlijst en extra zenders wanneer gegevens beschikbaar zijn. Zwitserland bevat de drie taalregio’s; België bevat Nederlandse en Franse zenders.

**Automatisch · Home Assistant** volgt eerst je profieltaal en daarna de installatie-instellingen. Zonder beschikbare taal kiest de gids Duits voor Duitsland en Oostenrijk en Nederlands voor Nederland en Noors voor Noorwegen. Voor meertalige landen wordt de browsertaal gebruikt; Engels is de terugvaltaal. Duits, Engels, Nederlands, Frans, Italiaans en Noors zijn ook handmatig te kiezen. De taal staat los van het tv-land. Programmatitels en beschrijvingen behouden hun oorspronkelijke taal.

## Je programma en zenders

Kies **Nu**, **20:15**, **22:00** of **Andere tijden**. Klik op een programma voor meer informatie. **Hoofdzenders** toont de voorbereide lijst. Via **☰ Zenders** kies en sorteer je **Mijn zenders**. Je persoonlijke keuze wordt per land bewaard; **Standaardvolgorde** herstelt de beginlijst.

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
