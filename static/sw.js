const CACHE_NAME = 'g-business-shell-v2';
const SHELL_RESOURCES = [
  '/',
  '/static/manifest.json',
  '/static/js/pwa.js'
];

// External CDN assets to cache on first visit (will be cached as opaque responses)
const EXTERNAL_ASSETS = [
  'https://cdn.tailwindcss.com',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
  'https://unpkg.com/htmx.org@1.9.10',
  'https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js'
];

// Add external assets to shell resources so they're cached during install
EXTERNAL_ASSETS.forEach(u => SHELL_RESOURCES.push(u));

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_RESOURCES))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

function networkFirst(request) {
  return fetch(request).then((resp) => {
    if (!resp || resp.status !== 200 || resp.type !== 'basic') return resp;
    const copy = resp.clone();
    caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
    return resp;
  }).catch(() => caches.match(request));
}

self.addEventListener('fetch', (event) => {
  const req = event.request;

  // API calls -> network first
  if (req.url.includes('/api/')) {
    event.respondWith(networkFirst(req));
    return;
  }

  // External CDN assets: cache-first
  if (EXTERNAL_ASSETS.some(u => req.url.startsWith(u))) {
    event.respondWith(
      caches.match(req).then(cached => cached || fetch(req).then(resp => {
        // store a copy
        const copy = resp.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(req, copy));
        return resp;
      }).catch(() => cached))
    );
    return;
  }

  // For navigation and static assets, try cache first
  event.respondWith(
    caches.match(req).then((cached) => cached || fetch(req).catch(() => {
      // fallback to cached index for navigation
      if (req.mode === 'navigate') return caches.match('/');
      return new Response('Offline', { status: 503, statusText: 'Offline' });
    }))
  );
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SYNC_NOW') {
    self.registration.sync && self.registration.sync.register('sync-queue').catch(()=>{});
  }
});
