const CACHE = "facturas-v2";
const SHELL = ["/static/css/app.css", "/static/js/app.js", "/static/espera.html"];
// Cold start de Render (ADR-0005 general): si una navegación (HTML) no
// responde dentro de este margen, servimos el shell de espera cacheado
// en su lugar — la navegación de red sigue corriendo en background, solo
// se ignora su resultado si perdió la carrera.
const TIMEOUT_NAVEGACION_MS = 3000;

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET") return;
  if (new URL(e.request.url).pathname.startsWith("/api/")) return;

  if (e.request.mode === "navigate") {
    // Carrera entre la red real y un timeout corto: si Render está
    // despertando (cold start, ~30s), no hacemos esperar al usuario con
    // una pantalla en blanco — le mostramos el shell de espera propio
    // (static/espera.html) apenas se cumple el margen, y ese shell hace
    // polling solo hasta que el backend responda de verdad.
    e.respondWith(
      Promise.race([
        fetch(e.request),
        new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), TIMEOUT_NAVEGACION_MS)),
      ]).catch(() => caches.match("/static/espera.html"))
    );
    return;
  }

  e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
});
