# Backend layout

- `services.py`: application context, configuration, channel preferences, logos, saved programmes, reminders and startup.
- `sources.py`: XMLTV mapping and schedule parsers for public programme sources.
- `timeline.py`: source priorities, programme merging, duplicate detection and coverage.
- `store.py`: country stores, persistent cache, refresh lifecycle and guide payloads.
- `api.py`: HTTP routes and static-file handling.
- `../app.py`: executable entry point.

`services.py` binds `EPGStore` and `Handler` to the same application context through their `runtime` attribute. The extracted classes read configuration and application state through that context; they do not import the application module back. This avoids circular imports and independent copies of the active country or store registry. Country changes update the shared context, while an in-flight request retains the store it selected at the start.

Modules import ordinary standard-library dependencies directly. The runtime context is reserved for application configuration, shared state and callbacks; the clock and HTTP opener remain replaceable through it for deterministic source and date tests. Do not route unrelated standard-library helpers through the services module.

Keep source parsing in `ProgrammeSources`, programme reconciliation in `ProgrammeTimeline`, and cache/refresh work in `GuideStore`. Preserve persisted file names, country separation, cache schema and HTTP responses when changing module boundaries. Tests that replace configuration or network calls should patch the services context used by both stores and handlers.

CI also runs `tests/container_smoke.py` inside each built image (amd64, aarch64, armv7), with external networking disabled. It verifies backend imports, bundled resources, persistent-cache reload and HTTP endpoints. The smoke test is supplied through stdin rather than copied into the production image.
