// Service Worker 清理脚本
// 用于注销旧的"减肥教练"项目 Service Worker，清除所有缓存
// 安装后立即接管并清理旧缓存

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          return caches.delete(cacheName);
        })
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// 不拦截任何请求，直接走网络
self.addEventListener('fetch', (event) => {
  event.respondWith(fetch(event.request));
});
