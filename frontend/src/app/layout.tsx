import type { Metadata } from 'next'
import './globals.css'

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
        {children}
      </body>
    </html>
  )
}
