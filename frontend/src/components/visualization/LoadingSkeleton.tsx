'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'

interface LoadingSkeletonProps {
  variant?: 'chart' | 'table' | 'simple'
}

export function LoadingSkeleton({ variant = 'simple' }: LoadingSkeletonProps) {
  if (variant === 'chart') {
    return (
      <Card>
        <CardHeader>
          <div className="animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-48 mb-2" />
            <div className="h-4 bg-gray-100 rounded w-32" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-center">
              <div className="w-40 h-40 rounded-full bg-gray-200 animate-pulse" />
            </div>
            <div className="space-y-2">
              <div className="h-4 bg-gray-100 rounded" />
              <div className="h-4 bg-gray-100 rounded w-5/6" />
              <div className="h-4 bg-gray-100 rounded w-4/6" />
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (variant === 'table') {
    return (
      <Card>
        <CardHeader>
          <div className="animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-48 mb-2" />
            <div className="h-4 bg-gray-100 rounded w-32" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-3">
                    <div className="h-4 bg-gray-200 rounded w-16 animate-pulse" />
                  </th>
                  <th className="text-center py-2 px-3">
                    <div className="h-4 bg-gray-200 rounded w-12 animate-pulse" />
                  </th>
                  <th className="text-center py-2 px-3">
                    <div className="h-4 bg-gray-200 rounded w-12 animate-pulse" />
                  </th>
                  <th className="text-center py-2 px-3">
                    <div className="h-4 bg-gray-200 rounded w-12 animate-pulse" />
                  </th>
                </tr>
              </thead>
              <tbody>
                {[1, 2, 3].map(i => (
                  <tr key={i} className="border-b border-gray-100">
                    <td className="py-2 px-3">
                      <div className="h-6 bg-gray-100 rounded w-20 animate-pulse" />
                    </td>
                    <td className="py-2 px-3">
                      <div className="h-6 bg-gray-100 rounded w-12 animate-pulse" />
                    </td>
                    <td className="py-2 px-3">
                      <div className="h-6 bg-gray-100 rounded w-12 animate-pulse" />
                    </td>
                    <td className="py-2 px-3">
                      <div className="h-6 bg-gray-100 rounded w-12 animate-pulse" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Simple variant
  return (
    <Card>
      <CardHeader>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-32" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="h-20 bg-gray-100 rounded animate-pulse" />
          <div className="h-4 bg-gray-100 rounded w-3/4" />
        </div>
      </CardContent>
    </Card>
  )
}
