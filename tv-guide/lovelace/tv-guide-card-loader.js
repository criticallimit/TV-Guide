// Stable Home Assistant resource loader for TV Guide.
// The generated card file already contains the shared renderer, so one import is enough.
// A changing query string prevents Home Assistant/browser caches from keeping an old card build.
import("/local/tv-guide-card.js?t=" + Date.now()).catch((err) => {
  console.error("[TV Guide] Lovelace card could not be loaded", err);
});
