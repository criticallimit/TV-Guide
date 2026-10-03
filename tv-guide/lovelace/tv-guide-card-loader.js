// Stable Home Assistant resource loader for TV Guide.
// Keep the module evaluation pending until both shared renderer and card are ready.
const stamp = Date.now();
await import("/local/tv-guide-core.js?ts=" + stamp);
await import("/local/tv-guide-card.js?ts=" + stamp);
