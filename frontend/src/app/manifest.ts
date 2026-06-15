import type { MetadataRoute } from 'next'

// Next.js가 /manifest.webmanifest 로 자동 서빙한다 (PWA 설치 메타데이터).
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'PCCS2 — 패드인쇄 색보정 시스템',
    short_name: 'PCCS2',
    description: 'AI 기반 잉크 배합비 추천·관리 시스템',
    start_url: '/',
    scope: '/',
    display: 'standalone',
    orientation: 'portrait',
    background_color: '#f9fafb',
    theme_color: '#0284c7',
    lang: 'ko',
    icons: [
      { src: '/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
      { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
      { src: '/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
    ],
  }
}
