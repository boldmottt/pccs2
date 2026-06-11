import type { Metadata } from 'next'
import './globals.css'
import { Providers } from '@/lib/providers/QueryClientProvider'
import { Navbar } from '@/components/layout/Navbar'

export const metadata: Metadata = {
  title: 'PCCS2 - Pad-print Color Correction System',
  description: 'AI-powered ink recipe recommendation system',
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
      </body>
    </html>
  )
}
