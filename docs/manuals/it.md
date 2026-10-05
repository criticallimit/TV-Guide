# TV Guide per Home Assistant

Consulta i programmi TV, organizza la serata e salva le trasmissioni con un promemoria. La guida funziona su schermi grandi e telefoni, con un aspetto chiaro o scuro.

## Installazione

Serve Home Assistant con lo store di app/add-on, ad esempio Home Assistant OS.

1. Apri **Impostazioni → App** (o **Componenti aggiuntivi**) e lo store.
2. Aggiungi `https://github.com/criticallimit/TV-Guide` in **Repository**.
3. Installa e avvia **TV Guide**, quindi attiva la visualizzazione nella barra laterale.
4. Apri **TV Guide**. Il primo caricamento dei programmi può richiedere alcuni minuti.

## Paese e lingua

Apri le impostazioni con il pulsante a forma di ingranaggio. In **Paese e lingua** scegli Germania, Austria, Svizzera, Paesi Bassi, Belgio, Norvegia o Francia. Ogni paese ha canali principali e altri canali quando sono disponibili i programmi. La Svizzera include le tre regioni linguistiche; il Belgio include canali in neerlandese e francese.

**Automatico · Home Assistant** usa prima la lingua del profilo e poi le impostazioni dell’installazione. Se non è disponibile una lingua, usa il tedesco per Germania e Austria e il neerlandese per i Paesi Bassi e il norvegese per la Norvegia e francese per la Francia. Per i paesi multilingue usa la lingua del browser, con l’inglese come alternativa. Puoi anche scegliere tedesco, inglese, neerlandese, francese, italiano o norvegese. Il paese dei programmi e la lingua dell’interfaccia sono indipendenti. Titoli e descrizioni mantengono la lingua originale.

## Programmi e canali

Scegli **Ora**, **18:00**, **20:15**, **22:00** o **Altri orari**. Tocca un programma per i dettagli. **Canali principali** mostra la lista preparata. Usa **☰ Canali** per scegliere e ordinare **I miei canali**. La selezione personale viene mantenuta quando cambi paese; **Ordine predefinito** ripristina la lista iniziale.

Le impostazioni sono divise in **Paese e lingua**, **Visualizzazione** e **Promemoria**. Imposta vista iniziale, aspetto e numero di canali in Visualizzazione. **0** mostra l’intera lista selezionata. L’intervallo di aggiornamento si trova in **Avanzate**. Premi **Salva** per applicare le modifiche.

## Salvare programmi e ricevere promemoria

Apri un programma e scegli **Salva**. Lo trovi in **★ Salvati**. Per un programma futuro salvato, attiva **Ricordamelo**, 5, 10, 15 o 30 minuti prima.

Nelle impostazioni apri **Promemoria**, scegli Home Assistant o un dispositivo mobile collegato e usa **Prova la notifica**. Home Assistant e TV Guide devono essere attivi al momento del promemoria. Il promemoria mantiene la lingua usata quando è stato creato.

## Sulla dashboard

Apri **Sulla dashboard** nelle impostazioni. In Home Assistant, apri **Impostazioni → Dashboard → Risorse** e aggiungi `/local/tv-guide-card-loader.js` come **Modulo JavaScript**. Attiva la modalità avanzata nel profilo se Risorse è nascosto. Ricarica Home Assistant e aggiungi la scheda TV Guide. Se la prima scheda non appare, riavvia Home Assistant una volta.

## Se manca qualcosa

La disponibilità dipende dalle fonti pubbliche. I dati confermati dalle emittenti hanno la priorità; altre fonti completano le informazioni mancanti. I Paesi Bassi usano attualmente una guida pubblica verificata. Non tutti i canali e i giorni sono sempre disponibili. Dopo un aggiornamento o un cambio di paese, attendi la fine del caricamento.

Se un promemoria non arriva, controlla il destinatario e invia una notifica di prova. I dispositivi mobili devono essere collegati all’app Home Assistant.

Installa gli aggiornamenti pubblicati dallo store. Le liste dei canali e i programmi salvati vengono mantenuti. Le modifiche su main possono precedere la prossima versione pubblicata.

[Segnala un problema](https://github.com/criticallimit/TV-Guide/issues) indicando paese, canale, data e ora.

La Francia include 24 canali nazionali principali. BFMTV è temporaneamente escluso.
