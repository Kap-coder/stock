const CACHE_NAME = 'g-business-shell-v3';
const SHELL_RESOURCES = [
  '/',
  '/static/manifest.json',
  '/static/js/pwa.js',
  '/static/css/app.css',
  '/static/offline.html',
  '/static/vendor/tailwind.js',
  '/static/vendor/fontawesome.min.css',
  '/static/vendor/htmx.min.js',
  '/static/vendor/alpine.min.js',
  '/static/vendor/alpine.min.js'
];

// External CDN assets to cache on first visit (will be cached as opaque responses)
// Vendor assets should be hosted locally at /static/vendor/*
// Populate them using scripts/download_vendors.py or download manually.

self.addEventListener('install', (event) => {
  event.waitUntil(
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      // Precache shell resources
      await cache.addAll(SHELL_RESOURCES);
      // No external CDN caching during install; vendors should be local under /static/vendor/
    })()
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    // remove old caches (keep only current)
    const keys = await caches.keys();
    await Promise.all(keys.map(k => { if (k !== CACHE_NAME) return caches.delete(k); }));
    // ensure we don't keep any potentially cached authenticated pages from previous installs
    const c = await caches.open(CACHE_NAME);
    try { await c.delete('/inventory/products/'); } catch(e){}
    try { await c.delete('/inventory/products/add/'); } catch(e){}
    await self.clients.claim();
  })());
});

function networkFirst(request) {
  return fetch(request).then((resp) => {
    if (!resp) return caches.match(request);
    // cache successful basic responses
    try {
      const ct = resp.headers.get('content-type') || '';
      if (resp.status === 200 && ct.indexOf('text/html') !== -1) {
        const copy = resp.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
      } else if (resp.status === 200 && resp.type === 'basic') {
        const copy = resp.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
      }
    } catch(e){}
    return resp;
  }).catch(() => caches.match(request));
}

function networkFirstNavigation(request) {
  return fetch(request).then((resp) => {
    if (resp && resp.status === 200) {
      const copy = resp.clone();
      caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
      return resp;
    }
    return caches.match(request).then(cached => cached || caches.match('/') );
  }).catch(() => caches.match(request).then(cached => cached || caches.match('/static/offline.html')));
}

self.addEventListener('fetch', (event) => {
  const req = event.request;

  // API calls -> network first
  if (req.url.includes('/api/')) {
    event.respondWith(networkFirst(req));
    return;
  }

  // Vendor assets are served from /static/vendor/ and handled by static asset caching below.

  // Navigation requests: network-first, then cache, then offline fallback
  if (req.mode === 'navigate') {
    event.respondWith(networkFirstNavigation(req));
    return;
  }

  // For static assets, try cache first
  event.respondWith(
    caches.match(req).then((cached) => cached || fetch(req).then(resp => {
      // runtime cache fetched resources for later
      try {
        if (resp && resp.status === 200) {
          const copy = resp.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(req, copy));
        }
      } catch(e){}
      return resp;
    }).catch(() => new Response('Offline', { status: 503, statusText: 'Offline' })))
  );
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SYNC_NOW') {
    self.registration.sync && self.registration.sync.register('sync-queue').catch(()=>{});
  }
});
