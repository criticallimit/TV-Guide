# TV Guide for Home Assistant

Se hva som går på TV nå, planlegg kvelden og lagre programmer med påminnelser. TV Guide fungerer på datamaskin, nettbrett og mobil, med lyst og mørkt utseende.

## Installer

Du trenger Home Assistant med app-/tilleggsbutikken, for eksempel Home Assistant OS.

1. Åpne **Innstillinger → Apper** (eller **Tillegg**) og deretter butikken.
2. Legg til `https://github.com/criticallimit/TV-Guide` under **Repositories**.
3. Installer og start **TV Guide**. Aktiver visning i sidepanelet.
4. Åpne **TV Guide**. Første innlasting av programdata kan ta noen minutter.

## Land og språk

Åpne innstillingene med tannhjulknappen. Under **Land og språk** kan du velge Tyskland, Østerrike, Sveits, Nederland, Belgia, Danmark, Norge, Frankrike eller Sverige. Hvert land har en egen liste med hovedkanaler og flere kanaler når programdata er tilgjengelige. Den personlige kanallisten beholdes når du bytter land.

**Automatisk · Home Assistant** bruker først profilspråket ditt og deretter språket i Home Assistant-installasjonen. Uten tilgjengelig språk brukes norsk for Norge, tysk for Tyskland og Østerrike, nederlandsk for Nederland, fransk for Frankrike og svensk for Sverige. Danmark bruker engelsk når ingen profilspråk er tilgjengelig. For flerspråklige land brukes nettleserspråket; engelsk er reservespråket. Du kan også velge tysk, engelsk, nederlandsk, fransk, italiensk, norsk bokmål eller svensk manuelt. Språket er uavhengig av TV-landet. Programtitler og beskrivelser beholder originalspråket.

## Programmer og kanaler

Velg **Nå**, **18:00**, **20:15**, **22:00** eller **Andre tider**. Klikk på et program for å se mer informasjon. **Hovedkanaler** viser den ferdige listen. Med **☰ Kanaler** velger og sorterer du **Mine kanaler**. **Tilbakestill rekkefølgen** gjenoppretter standardlisten for det valgte landet.

Du kan velge antall kanaler per rad og hvor mange som skal vises. Verdien **0** viser hele den valgte kanallisten. Når du ruller, flyttes visningen til neste kanalrad, også den siste raden.

## Lagre og få påminnelser

Åpne et program og velg **☆ Lagre**. Lagrede programmer finner du med **★ Lagret**. Aktiver **Minn meg på** for å få et varsel 5, 10, 15 eller 30 minutter før programmet begynner. Påminnelser gjelder kommende programmer.

Under **Påminnelser** i innstillingene velger du Home Assistant eller en tilkoblet mobilenhet. Bruk **Test varsel** for å sjekke mottakeren. TV Guide må kjøre for at påminnelsene skal sendes.

## På dashbordet

Åpne **På dashbordet** i innstillingene og følg trinnene som vises der. Kopier ressursadressen, åpne **Innstillinger → Dashbord → Ressurser** og legg den til som en **JavaScript-modul**. Last Home Assistant på nytt og legg til **TV Guide** fra kortvelgeren.

## Hvis noe mangler

Hvis en kanal mangler programdata for valgt tidspunkt, viser TV Guide dette i stedet for å bruke gamle programmer. Prøv igjen etter en oppdatering. Kildene kan ha ulik dekning for kommende dager.

Hvis en gammel lenke åpner feilen «App docs does not exist», gå tilbake til appbutikken og se etter oppdateringer for repositoriene. Åpne deretter TV Guide igjen. [Alle brukerveiledninger](https://criticallimit.github.io/TV-Guide/manuals/nb.html) kan også åpnes direkte i nettleseren.

[Meld fra om et problem](https://github.com/criticallimit/TV-Guide/issues) og oppgi land, kanal, dato og tidspunkt.

Frankrike har 24 nasjonale hovedkanaler. BFMTV er foreløpig utelatt.
