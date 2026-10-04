# Backend layout

- `services.py`: application context, configuration, channel preferences, logos, saved programmes, reminders and startup.
- `sources.py`: XMLTV mapping and schedule parsers for public programme sources.
- `timeline.py`: source priorities, programme merging, duplicate detection and coverage.
- `store.py`: country stores, persistent cache, refresh lifecycle and guide payloads.
- `api.py`: HTTP routes and static-file handling.
- `../app.py`: executable entry point.

`services.py` binds `EPGStore` and `Handler` to the same application context through their `runtime` attribute. The extracted classes read configuration and application state through that context; they do not import the application module back. This avoids circular imports and independent copies of the active country or store registry. Country changes update the shared context, while an in-flight request retains the store it selected at the start.

Keep source parsing in `ProgrammeSources`, programme reconciliation in `ProgrammeTimeline`, and cache/refresh work in `GuideStore`. Preserve persisted file names, country separation, cache schema and HTTP responses when changing module boundaries. Tests that replace configuration or network calls should patch the services context used by both stores and handlers.
