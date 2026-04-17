'use client'

import Link from 'next/link'
import { cn } from '@/lib/utils'

export default function Home() {
  const features = [
    {
      name: 'Projects',
      description: '프로젝트 관리',
      href: '/projects',
      gradient: 'from-violet-500 to-fuchsia-500',
    },
    {
      name: 'Samples',
      description: '샘플 배합비 관리',
      href: '/samples',
      gradient: 'from-cyan-500 to-blue-500',
    },
    {
      name: 'Inks',
      description: '잉크 마스터 데이터',
      href: '/inks',
      gradient: 'from-emerald-500 to-teal-500',
    },
  ]

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 py-24 sm:px-6 lg:px-8 lg:py-32">
          <div className="text-center animate-fade-in">
            <h1 className="text-hero font-bold text-gradient mb-6">
              PCCS2
            </h1>
            <p className="text-2xl text-text-secondary max-w-2xl mx-auto">
              빅데이터 기반 AI 잉크 배합비 추천 시스템
            </p>
          </div>
        </div>

        {/* Subtle glow background */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-accent-primary/10 blur-[120px] rounded-full pointer-events-none" />
      </div>

      {/* Feature Cards */}
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-24">
        <div className="grid md:grid-cols-3 gap-6">
          {features.map((feature) => (
            <Link
              key={feature.name}
              href={feature.href}
              className="group relative"
            >
              <div className="absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-10 transition-opacity duration-[--duration-normal] rounded-xl" style={{ background: `linear-gradient(to bottom right, var(--accent-primary), var(--accent-secondary))` }} />
              <div className="relative h-full bg-bg-secondary/50 backdrop-blur-sm border border-border-subtle rounded-xl p-8 hover:shadow-xl hover:shadow-accent-primary/10 hover:-translate-y-1 transition-all duration-[--duration-normal]">
                <div className="mb-4">
                  <span className={cn(
                    'inline-block px-3 py-1 rounded-full text-sm font-medium bg-gradient-to-r',
                    feature.gradient,
                    'text-white'
                  )}>
                    {feature.name}
                  </span>
                </div>
                <h3 className="text-xl font-semibold mb-2">{feature.name}</h3>
                <p className="text-text-secondary">{feature.description}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
