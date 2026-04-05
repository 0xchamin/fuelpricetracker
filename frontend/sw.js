const CACHE_NAME = 'fueltracker-v1';
const STATIC_ASSETS = ['/', '/assets/styles.css', '/assets/icon-fuel.svg', '/assets/icon-ev.svg'];

self.addEventListener('install', e => {
    e.waitUntil(caches.open(CACHE_NAME).then(c => c.addAll(STATIC_ASSETS)));
    self.skipWaiting();
});

self.addEventListener('activate', e => {
    e.waitUntil(caches.keys().then(keys =>
        Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ));
    self.clients.claim();
});

self.addEventListener('fetch', e => {
    if (e.request.url.includes('/api/')) {
        e.respondWith(fetch(e.request).catch(() =>
            new Response('{"error":"offline"}', { headers: { 'Content-Type': 'application/json' } })
        ));
        return;
    }
    e.respondWith(caches.match(e.request).then(cached => cached || fetch(e.request)));
});

self.addEventListener('push', e => {
    const data = e.data?.json() || { title: 'FuelTracker', body: 'Time to submit a fuel price! ⛽' };
    e.waitUntil(self.registration.showNotification(data.title, {
        body: data.body,
        icon: '/assets/icon-192.png',
        badge: '/assets/icon-192.png',
        tag: 'fuel-reminder',
        renotify: true,
    }));
});

self.addEventListener('notificationclick', e => {
    e.notification.close();
    e.waitUntil(clients.openWindow('/'));
});
