const CACHE = "fittrack-v1";
const STATIC = [
  "/",
  "/activities",
  "/health",
  "/stats",
  "/upload",
  "/static/css/app.css",
  "/static/js/api.js",
  "/static/js/dashboard.js",
  "/static/js/upload.js",
  "/static/js/activities.js",
  "/static/js/health.js",
  "/static/js/stats.js",
  "/manifest.json",
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(STATIC)));
  self.skipWaiting();
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  // Always fetch API calls from network
  if (url.pathname.startsWith("/api/")) {
    e.respondWith(fetch(e.request));
    return;
  }
  // Static: cache-first
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
