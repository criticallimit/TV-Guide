// Stable Home Assistant resource loader for TV Guide.
// Ingress and Lovelace share the same renderer. Load it first, then the card.
const stamp = Date.now();
import("/local/tv-guide-core.js?ts=" + stamp)
  .then(() => import("/local/tv-guide-card.js?ts=" + stamp))
  .catch((err) => {
    console.error("[TV Guide] Lovelace card could not be loaded", err);
  });
