// Stable Home Assistant resource loader for TV Guide.
// The card itself opens the add-on through Home Assistant's Supervisor Ingress.
// A changing query string prevents browser caches from keeping an old card build.
import("/local/tv-guide-card.js?t=" + Date.now()).catch((err) => {
  console.error("[TV Guide] Lovelace card could not be loaded", err);
});
