// PCCS2 PWA 서비스워커 — 앱 셸을 가볍게 캐시해 설치 가능하게 만든다.
// 데이터(백엔드 API)는 항상 네트워크에서 가져와 신선도를 유지한다.
const CACHE = 'pccs2-shell-v1'
const SHELL = ['/']

self.addEventListener('install', event => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then(c => c.addAll(SHELL))
      .then(() => self.skipWaiting()),
  )
})

self.addEventListener('activate', event => {
  event.waitUntil(
    caches
      .keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', event => {
  const { request } = event
  if (request.method !== 'GET') return

  const url = new URL(request.url)
  // 크로스오리진(백엔드 API 등)·/api 경로는 가로채지 않는다 — 항상 네트워크.
  if (url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return

  // 페이지 내비게이션: 네트워크 우선, 오프라인이면 캐시된 셸로 폴백.
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(() => caches.match('/')))
    return
  }

  // 정적 자산: 캐시 우선 + 백그라운드 갱신(stale-while-revalidate).
  event.respondWith(
    caches.match(request).then(cached => {
      const network = fetch(request)
        .then(res => {
          if (res && res.status === 200) {
            const clone = res.clone()
            caches.open(CACHE).then(c => c.put(request, clone))
          }
          return res
        })
        .catch(() => cached)
      return cached || network
    }),
  )
})
