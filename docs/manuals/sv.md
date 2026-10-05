# TV Guide för Home Assistant

Se vad som går på TV nu, planera kvällen, spara program och få påminnelser. TV Guide fungerar på dator och mobil, med ljust och mörkt tema som kan följa Home Assistant.

[Dansk](https://criticallimit.github.io/TV-Guide/manuals/da.html) · [Deutsch](https://criticallimit.github.io/TV-Guide/manuals/de.html) · [English](https://criticallimit.github.io/TV-Guide/manuals/en.html) · [Español](https://criticallimit.github.io/TV-Guide/manuals/es.html) · [Nederlands](https://criticallimit.github.io/TV-Guide/manuals/nl.html) · [Français](https://criticallimit.github.io/TV-Guide/manuals/fr.html) · [Italiano](https://criticallimit.github.io/TV-Guide/manuals/it.html) · [Norsk](https://criticallimit.github.io/TV-Guide/manuals/nb.html) · [Svenska](https://criticallimit.github.io/TV-Guide/manuals/sv.html)

## Det här kan du göra

- Välj **Tyskland, Österrike, Schweiz, Nederländerna, Belgien, Danmark, Norge, Frankrike eller Sverige**. Varje land har förberedda huvudkanaler och ytterligare kanaler när programdata finns.
- Öppna **Nu**, **18:00**, **20:15**, **22:00** eller välj en annan dag och tid.
- Skapa **Mina kanaler** med eget urval och egen ordning. Kombinera kanaler från alla länder som stöds i en personlig lista.
- Öppna ett program för detaljer, spara det och skapa en påminnelse 5, 10, 15 eller 30 minuter innan det börjar.
- Använd **tyska, engelska, nederländska, franska, italienska, norska eller svenska**. Det automatiska valet följer ditt Home Assistant-profil.

Sverige har 16 förberedda huvudkanaler. SVT1, SVT2, SVT Barn, Kunskapskanalen och SVT24 kompletteras med SVT:s officiella programguide när den är tillgänglig.

## Installation

Du behöver Home Assistant med app-/add-on-butiken, till exempel Home Assistant OS.

1. Öppna **Inställningar → Appar** (eller **Add-ons**) och butiken.
2. Lägg till `https://github.com/criticallimit/TV-Guide` under **Repositories**.
3. Installera och starta **TV Guide**.
4. Aktivera **Visa i sidofältet** och öppna **TV Guide**.

[Lägg till repositoryt i Home Assistant](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fcriticallimit%2FTV-Guide)

Guiden öppnas medan programdata hämtas. Den första hämtningen kan ta några minuter.

## Land och språk

Öppna **inställningarna** och välj **Land och språk**. Välj landet vars TV-tablå du vill se. Schweiz innehåller kanaler från tre språkregioner och Belgien innehåller både nederländska och franska kanaler.

**Automatiskt · Home Assistant** använder först språket i ditt Home Assistant-profil och därefter installationsinställningarna. Om inget språk är tillgängligt används tyska för Tyskland och Österrike, nederländska för Nederländerna, norska för Norge, franska för Frankrike och svenska för Sverige. Engelska används som reserv. Du kan också välja språk manuellt.

Land och språk är oberoende av varandra. Programtitlar och beskrivningar behålls på källspråket. En påminnelse behåller språket som användes när den skapades.

## Anpassa guiden

**Huvudkanaler** visar den förberedda listan för valt TV-land. Öppna **☰ Kanaler**, markera länderna du vill bläddra i och sök efter en kanal. Lägg till kanaler under **Mina kanaler** och dra dem eller använd pilarna för att ändra ordningen. Om ett land avmarkeras döljs bara de tillgängliga kanalerna; redan valda kanaler behålls.

Inställningarna är grupperade i **Land och språk**, **Vy**, **Påminnelser** och **Avancerat**. Du kan välja standardvy, utseende, antal kanaler per rad och uppdateringsintervall. Ett kanalantal på **0** visar hela den valda listan.

## Spara program och få påminnelser

Öppna ett program och välj **Spara**. Sparade program finns under **★ Sparad**. För ett framtida program kan du aktivera **Påminn** och välja hur långt i förväg du vill bli aviserad.

Under **Påminnelser** kan du välja Home Assistant eller en ansluten mobilenhet. Använd **Testa avisering** för att kontrollera mottagaren. TV Guide och Home Assistant måste vara igång när påminnelsen ska skickas.

## Lägg till dashboard-kortet

Sidofältet kräver ingen extra konfiguration. För dashboarden:

1. Öppna **På dashboarden** i TV Guide-inställningarna.
2. I Home Assistant öppnar du **Inställningar → Dashboards → Resurser**.
3. Lägg till `/local/tv-guide-card-loader.js` som **JavaScript-modul**.
4. Ladda om Home Assistant och lägg till kortet **TV Guide**.

Om detta är din första dashboard-resurs och kortet saknas kan Home Assistant behöva startas om en gång.

## Om något saknas

**Ingen programinformation för en kanal:** Tillgängligheten beror på offentliga källor. Bekräftade uppgifter från TV-bolag prioriteras och andra flöden används för att fylla luckor.

**Tom guide efter uppdatering eller landsbyte:** Låt hämtningen slutföras och öppna guiden igen efter några minuter.

**Ingen påminnelse:** Kontrollera mottagaren i inställningarna och skicka en testavisering.

## Uppdateringar och hjälp

Installera publicerade uppdateringar via Home Assistant-butiken. Ändringar på `main` kan finnas där före nästa release.

[Rapportera ett problem](https://github.com/criticallimit/TV-Guide/issues) och ange land, kanal, datum och tid.
