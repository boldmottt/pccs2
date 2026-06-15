'use client'

import { useEffect } from 'react'

/** 서비스워커를 등록해 앱을 설치 가능하게 만든다 (프로덕션 빌드에서만). */
export function ServiceWorkerRegister() {
  useEffect(() => {
    if (
      typeof navigator !== 'undefined' &&
      'serviceWorker' in navigator &&
      process.env.NODE_ENV === 'production'
    ) {
      navigator.serviceWorker.register('/sw.js').catch(() => {
        /* 등록 실패는 조용히 무시 — 설치형 기능만 비활성화될 뿐 앱은 정상 동작 */
      })
    }
  }, [])

  return null
}
