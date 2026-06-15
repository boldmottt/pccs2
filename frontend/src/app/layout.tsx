import type { Metadata, Viewport } from 'next'
import './globals.css'
import { Providers } from '@/lib/providers/QueryClientProvider'
import { Navbar } from '@/components/layout/Navbar'
import { ServiceWorkerRegister } from '@/components/pwa/ServiceWorkerRegister'

export const metadata: Metadata = {
  title: 'PCCS2 — 패드인쇄 색보정 시스템',
  description: 'AI 기반 잉크 배합비 추천·관리 시스템',
  manifest: '/manifest.webmanifest',
  applicationName: 'PCCS2',
  appleWebApp: { capable: true, statusBarStyle: 'default', title: 'PCCS2' },
  icons: {
    icon: '/icon-192.png',
    apple: '/apple-touch-icon.png',
  },
}

export const viewport: Viewport = {
  themeColor: '#0284c7',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  viewportFit: 'cover',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gray-50">
        <Providers>
          <Navbar />
          {children}
        </Providers>
        <ServiceWorkerRegister />
      </body>
    </html>
  )
}
