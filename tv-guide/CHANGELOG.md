# Changelog

## 1.1.8

- Added the United Kingdom with Europe/London schedules, 20 curated main channels, exact XMLTV identities and English language selection throughout ingress, Home Assistant settings and public documentation.
- Expanded reviewed offline logo coverage with 795 channel assignments and 264 higher-resolution images, prepared for light and dark themes. All 246 main channels have real artwork; the inspected live catalog has artwork for 3,869 of 3,919 channels (98.72%). The remaining 50 additional channels use readable name fallbacks.
- Invalidated browser and generated logo caches when artwork assignments or bundled image contents change, including Europe-pack images replaced at an existing path.
- Corrected the Channel 5 HD fallback and daylight-saving transitions in XMLTV schedules, timelines, reminders and optional sensors. Notification times now respect the Home Assistant timezone.
- Made country, flag, documentation and translation checks follow the actual country definitions; corrected browser test isolation for deferred logos.
- Validated the add-on for amd64 and aarch64 only. Python, Chromium/WebKit and both container build and smoke checks gate publication.

## 1.1.7

- Document the five optional automation sensors in the repository README, add-on information and add-on README.
- Match the sensor descriptions in the Home Assistant add-on configuration to the ingress settings in all eight languages.
- Keep the settings header and actions outside the scrolling content so sensor switches remain reachable in short card and ingress windows.
- Include the installed add-on version in the dashboard iframe URL to avoid reusing an older entry page after updates.

## 1.1.6

- Made optional sensors clearer in ingress and dashboard card settings: Advanced → Available sensors, with individual switches and descriptions.
- Revalidate the entry page and refresh frontend asset URLs after updates to avoid stale settings controls.

## 1.1.5

- Added five optional Home Assistant sensor states, individually enabled in Settings → Advanced.
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
