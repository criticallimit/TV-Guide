// Stable Home Assistant resource loader for TV Guide.
// The actual card is imported with a cache-busting query so add-on updates
// do not require the user to change the Lovelace resource URL.
import("/local/tv-guide-card.js?ts=" + Date.now()).catch((err) => {
  console.error("[TV Guide] Lovelace card could not be loaded", err);
});
