# TV Guide for Home Assistant

See what is on TV now, plan your evening, save programmes and get reminders. TV Guide works on desktop and mobile, with light and dark themes that can follow Home Assistant.

[Deutsch](https://criticallimit.github.io/TV-Guide/manuals/de.html) · [English](https://criticallimit.github.io/TV-Guide/manuals/en.html) · [Nederlands](https://criticallimit.github.io/TV-Guide/manuals/nl.html) · [Français](https://criticallimit.github.io/TV-Guide/manuals/fr.html) · [Italiano](https://criticallimit.github.io/TV-Guide/manuals/it.html) · [Norsk](https://criticallimit.github.io/TV-Guide/manuals/nb.html)

## Available countries

**🇩🇪 Germany · 🇦🇹 Austria · 🇨🇭 Switzerland · 🇳🇱 Netherlands · 🇧🇪 Belgium · 🇳🇴 Norway · 🇫🇷 France**

All seven countries have prepared main-channel lists, individual channel selections and local channel logos for light and dark themes. Switzerland includes its three language regions; Belgium includes Dutch- and French-language channels. Schedule availability depends on the channel and public source. France includes 24 national main channels; BFMTV is temporarily excluded.

**More countries are planned.** New countries will be added when reliable, publicly available programme data can be supported.

## What you can do

- Choose **Germany, Austria, Switzerland, the Netherlands, Belgium, Norway or France**. Each country has prepared main channels and additional channels when schedule data is available.
- Open **Now**, **20:15**, **22:00**, or choose another day and time.
- Create **My channels** with your own selection and order. Combine channels from all supported countries in one personal list. Your selection stays when you change country.
- Open a programme for details, save it and set a reminder 5, 10, 15 or 30 minutes before it starts.
- Use **German, English, Dutch, French, Italian or Norwegian**. The automatic setting follows your Home Assistant profile.

## Install

You need Home Assistant with the app/add-on store, such as Home Assistant OS.

1. Open **Settings → Apps** (or **Add-ons**) and the store.
2. Add `https://github.com/criticallimit/TV-Guide` to **Repositories**.
3. Install and start **TV Guide**.
4. Enable **Show in sidebar** and open **TV Guide**.

[Add the repository in Home Assistant](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fcriticallimit%2FTV-Guide)

The guide opens while schedules load. The first download can take a few minutes.

## Country and language

Open the **settings button** and select **Country & language**. Select the country whose TV schedules you want to see. Switzerland includes channels from its three language regions; Belgium includes Dutch- and French-language channels.

**Automatic · Home Assistant** uses your Home Assistant profile language first, then your installation settings. If no language is available, Germany and Austria use German, the Netherlands uses Dutch and Norway uses Norwegian and France uses French. For multilingual countries, the browser language is used; English is the fallback. You can also choose a language manually.

Country and language are independent: Swiss schedules can be displayed with a French or English interface. Programme titles and descriptions stay in the source language. A reminder keeps the language used when you created it.

## Personalize the guide

**Main channels** shows the prepared list for your TV country. Open **☰ Channels**, tick the countries you want to browse and search for a channel. Add channels to **My channels** and drag them or use the arrows to set their order. Unticking a country only hides its available channels; it keeps your selected channels. Remove a channel with **×**, then save. **Reset order** restores the main channels of the currently selected TV country. Your previous selection is carried over when you first save the new list.

Settings are grouped into **Country & language**, **Display** and **Reminders**. Set the default view, appearance and channels per row under **Display**. A channel limit of **0** shows the entire selected list. Open **Advanced** to change the schedule refresh interval. Press **Save** to apply your changes.

## Save programmes and get reminders

Open a programme and select **Save**. Find saved programmes under **★ Saved**. For a saved future programme, enable **Remind me** and choose how early to be notified.

In settings, open **Reminders** and choose Home Assistant or a connected mobile device. Use **Test notification** to check the destination. TV Guide and Home Assistant must be running when the reminder is due.

Your saved programmes and channel lists are available on devices using the same Home Assistant installation and survive restarts and updates.

## Add the dashboard card

The sidebar needs no extra setup. For your dashboard:

1. Open **On your dashboard** in TV Guide settings.
2. In Home Assistant, open **Settings → Dashboards → Resources**. Enable advanced mode in your profile if Resources is hidden.
3. Add `/local/tv-guide-card-loader.js` as a **JavaScript module**.
4. Reload Home Assistant and add the **TV Guide** card.

If this is your first dashboard resource and the card is missing, restart Home Assistant once. The card help in TV Guide lets you check the setup and copy the resource address.

## When something is missing

**No programme for a channel:** Availability depends on public sources. Confirmed broadcaster data is preferred; other feeds fill gaps. Coverage and updates vary by channel and date. The Netherlands currently uses a checked public programme feed.

**Empty guide after an update or country change:** Let the download finish and reopen the guide after a few minutes.

**No reminder:** Check the destination in settings and send a test notification. Mobile reminders need a device connected to the Home Assistant app.

## Updates and help

Install published updates through the Home Assistant app/add-on store. Changes on the main branch may arrive before the next release.

[Report an issue](https://github.com/criticallimit/TV-Guide/issues) and include the country, channel, date and time.
