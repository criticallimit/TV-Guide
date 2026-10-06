# Changelog

## 1.1.7

- Document the five optional automation sensors in the repository README, add-on information and add-on README.
- Match the sensor descriptions in the Home Assistant add-on configuration to the ingress settings in all eight languages.
- Keep the settings header and actions outside the scrolling content so sensor switches remain reachable in short card and ingress windows.
- Include the installed add-on version in the dashboard iframe URL to avoid reusing an older entry page after updates.

## 1.1.6

- Made optional sensors clearer in ingress and dashboard card settings: Advanced → Available sensors, with individual switches and descriptions.
- Revalidate the entry page and refresh frontend asset URLs after updates to avoid stale settings controls.

## 1.1.5

- Added five optional Home Assistant sensor states, individually enabled in Settings → Advanced. No MQTT or additional integration is required.
- Isolated sensor publishing from guide requests, with restart recovery, removal of disabled states and protection against existing foreign entity IDs.
- Reduced card startup waits and deferred offscreen channel logos.
- Protected settings, bookmarks and reminders against stale asynchronous responses.

## 1.1.4

- Added Denmark with a curated main-channel list and Danish programme data.
- Added complete Danish user-interface support and Danish documentation.
- Added sequential background preloading for inactive-country EPG caches with a two-minute pause between countries.
- Completed GitHub Pages and manual language coverage, including the Italian landing page and Spanish manual.
- Added consistency checks for countries, languages, public pages and manuals.

## 1.1.3

- Added Sweden with a curated main-channel list and Swedish programme sources.
- Added complete Swedish user-interface support.
- Added official SVT schedule enrichment with XMLTV fallback.
- Added the Europe-wide offline channel-logo library with prepared light and dark variants.
- Disabled runtime downloads of external channel logos.
- Sorted country selections and country lists alphabetically for the active language.
- Updated add-on information, documentation and GitHub Pages.
