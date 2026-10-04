# Changelog

## Unreleased

- Removes unused programme helpers, obsolete ordering/title-search routines and duplicate frontend formatting/escaping code.

- Pauses periodic browser work while the guide is hidden and refreshes when it becomes visible.
- Preserves unchanged programme elements and uses one shared programme click handler.
- Handles large programme lists without exceeding browser argument limits and clears stale date limits after a country change.
- Reduces repeated backend calculations and API response size.
- Reuses time and date formatters for each language instead of constructing them for every programme.

## 1.0.9

- Shows the TV Guide logo in the Home Assistant dashboard card picker.
- Highlights the six supported countries and plans for further countries in the README.

- Corrects series titles and episode subtitles from RTL-group schedules and excludes unrelated live-TV teasers. Rebuilds affected cached records while retaining other sources.

- Adds a local channel logo library for all six countries, with consistent light and dark variants.
- Adds Norwegian Bokmål throughout the app, settings, reminders, dashboard card and user guides.
- Fixes user-guide links opened from Home Assistant.

- Adds Norway with 20 main channels, direct NRK and TV 2 schedules and a public programme guide for remaining main channels.

- Adds direct NPO, VRT and VTM schedules and extends broadcaster coverage for shared public channels in Austria and Switzerland.
- Uses the complete Veronica / Disney Jr. schedule and reports main-channel coverage separately for current programmes and upcoming days.

- Adds channel lists and schedules for Austria, Switzerland, the Netherlands and Belgium, with separate channel preferences for each country.
- Adds German, English, Dutch, French and Italian interfaces, automatic Home Assistant language selection and translated user guides.
- Makes all settings sections collapsible, with aligned controls and accessible save buttons on desktop and mobile.
- Scrolls by channel row, including the final row, while keeping space below the fixed header.
- Adds the new TV Guide app icon, transparent logo and browser icon.
- Reduces routine request logging.

## 1.0.8

- Prefers confirmed broadcaster schedules and prevents programmes from different sources or dates from being mixed.
- Removes teletext markers and page references from programme titles.
- Keeps the navigation visible while scrolling and simplifies the programme overview.
- Improves dashboard card startup, settings persistence and use with blocked browser storage.
- Shows failed save actions clearly and handles malformed schedule times more reliably.
- Updates installation, channel list, reminder and dashboard instructions.
