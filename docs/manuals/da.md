# TV Guide til Home Assistant

Se hvad der er i TV nu, planlæg aftenen, gem programmer og få påmindelser. TV Guide fungerer på computer og mobil med lys og mørk visning, som kan følge Home Assistant.

[Dansk](https://criticallimit.github.io/TV-Guide/manuals/da.html) · [Deutsch](https://criticallimit.github.io/TV-Guide/manuals/de.html) · [English](https://criticallimit.github.io/TV-Guide/manuals/en.html) · [Español](https://criticallimit.github.io/TV-Guide/manuals/es.html) · [Nederlands](https://criticallimit.github.io/TV-Guide/manuals/nl.html) · [Français](https://criticallimit.github.io/TV-Guide/manuals/fr.html) · [Italiano](https://criticallimit.github.io/TV-Guide/manuals/it.html) · [Norsk](https://criticallimit.github.io/TV-Guide/manuals/nb.html) · [Svenska](https://criticallimit.github.io/TV-Guide/manuals/sv.html)

## Det kan du gøre

- Vælg **Tyskland, Østrig, Schweiz, Nederlandene, Belgien, Danmark, Norge, Frankrig eller Sverige**. Hvert land har en forberedt liste over hovedkanaler og flere kanaler, når programdata er tilgængelige.
- Åbn **Nu**, **18:00**, **20:15**, **22:00**, eller vælg en anden dag og tid.
- Opret **Mine kanaler** med dit eget udvalg og din egen rækkefølge. Du kan kombinere kanaler fra alle understøttede lande.
- Åbn et program for detaljer, gem det og opret en påmindelse 5, 10, 15 eller 30 minutter før start.
- Brug **dansk, tysk, engelsk, nederlandsk, fransk, italiensk, norsk eller svensk**. Automatisk følger dit Home Assistant-profil.

## Installation

Du skal bruge Home Assistant med App/Add-on Store, f.eks. Home Assistant OS.

1. Åbn **Indstillinger → Apps** (eller **Add-ons**) og butikken.
2. Tilføj `https://github.com/criticallimit/TV-Guide` under **Repositories**.
3. Installér og start **TV Guide**.
4. Aktivér **Vis i sidepanelet** og åbn **TV Guide**.

[Tilføj repositoryet i Home Assistant](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fcriticallimit%2FTV-Guide)

Guiden åbner, mens programdata hentes. Den første hentning kan tage nogle minutter.

## Land og sprog

Åbn **indstillingerne** og vælg **Land og sprog**. Vælg det land, hvis TV-program du vil se. Schweiz indeholder kanaler fra tre sprogområder, og Belgien indeholder både nederlandsk- og fransksprogede kanaler.

**Automatisk · Home Assistant** bruger først sproget i dit Home Assistant-profil og derefter installationsindstillingerne. Hvis intet profilsprog er tilgængeligt, bruges dansk for Danmark, tysk for Tyskland og Østrig, nederlandsk for Nederlandene, norsk for Norge, fransk for Frankrig og svensk for Sverige. Engelsk bruges som reserve.

Land og sprog er uafhængige af hinanden. Programtitler og beskrivelser bevarer kildens sprog. En påmindelse beholder det sprog, der blev brugt, da den blev oprettet.

## Tilpas guiden

**Hovedkanaler** viser den forberedte liste for det valgte TV-land. Åbn **☰ Kanaler**, markér de lande du vil gennemse, og søg efter en kanal. Tilføj kanaler til **Mine kanaler**, og træk dem eller brug pilene til at ændre rækkefølgen. Hvis et land fjernes fra filteret, skjules dets tilgængelige kanaler kun; allerede valgte kanaler bevares.

Indstillingerne er grupperet i **Land og sprog**, **Visning**, **Påmindelser** og **Avanceret**. Du kan vælge standardvisning, udseende, antal kanaler pr. række og opdateringsinterval. Et kanalantal på **0** viser hele den valgte liste.

## Gem programmer og få påmindelser

Åbn et program og vælg **Gem**. Gemte programmer findes under **★ Gemt**. For et fremtidigt program kan du aktivere en påmindelse og vælge, hvor tidligt du vil have besked.

Under **Påmindelser** kan du vælge Home Assistant eller en tilsluttet mobilenhed. Brug **Test notifikation** for at kontrollere modtageren. TV Guide og Home Assistant skal køre, når påmindelsen skal sendes.

## Tilføj dashboard-kortet

Sidepanelet kræver ingen ekstra opsætning. Til dashboardet:

1. Åbn **På dashboardet** i TV Guide-indstillingerne.
2. Åbn **Indstillinger → Dashboards → Ressourcer** i Home Assistant.
3. Tilføj `/local/tv-guide-card-loader.js` som **JavaScript-modul**.
4. Genindlæs Home Assistant og tilføj kortet **TV Guide**.

## Hvis noget mangler

**Ingen programdata for en kanal:** Tilgængeligheden afhænger af offentlige kilder. Bekræftede data fra TV-stationer prioriteres, og andre kilder udfylder huller.

**Tom guide efter opdatering eller skift af land:** Vent til hentningen er færdig, og åbn guiden igen efter nogle minutter.

**Ingen påmindelse:** Kontrollér modtageren i indstillingerne og send en testnotifikation.

## Opdateringer og hjælp

Installér publicerede opdateringer via Home Assistant-butikken. Ændringer på `main` kan være tilgængelige før næste release.

[Rapportér et problem](https://github.com/criticallimit/TV-Guide/issues) og angiv land, kanal, dato og klokkeslæt.
