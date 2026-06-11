'use client'

import { useRef, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient, getErrorMessage } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Database, Upload, CheckCircle2 } from 'lucide-react'

interface RdpImportResult {
  projects_created: number
  patterns_created: number
  rounds_created: number
  samples_created: number
  samples_skipped: number
  inks_created: number
  total_rows: number
}

const RESULT_LABELS: Array<{ key: keyof RdpImportResult; label: string }> = [
  { key: 'total_rows', label: '전체 배합 행' },
  { key: 'projects_created', label: '프로젝트 생성' },
  { key: 'patterns_created', label: '패턴 생성' },
  { key: 'rounds_created', label: '라운드 생성' },
  { key: 'samples_created', label: '샘플 생성' },
  { key: 'samples_skipped', label: '중복 건너뜀' },
  { key: 'inks_created', label: '잉크 자동 등록' },
]

export default function ImportPage() {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const importMutation = useMutation({
    mutationFn: (file: File) => apiClient.postFile<RdpImportResult>('/api/import/rdp', file),
    onSuccess: () => {
      queryClient.invalidateQueries()
    },
  })

  const result = importMutation.data

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-2">
        <Database className="w-7 h-7 text-blue-600" />
        <h1 className="text-2xl font-bold text-gray-900">RDP-DB 가져오기</h1>
      </div>
      <p className="text-gray-500 mb-8">
        작업일지에서 추출한 RDP 배합비 DB(<code className="text-sm bg-gray-100 px-1 rounded">rdp.db</code>)를
        업로드하면 프로젝트 → 패턴 → 라운드 → 샘플 계층으로 변환됩니다.
        이미 가져온 배합은 자동으로 건너뛰므로 같은 파일을 반복 업로드해도 안전합니다.
      </p>

      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <input
          ref={fileInputRef}
          type="file"
          accept=".db,.sqlite,.sqlite3"
          className="hidden"
          onChange={(e) => {
            setSelectedFile(e.target.files?.[0] ?? null)
            importMutation.reset()
          }}
        />
        <div className="flex items-center gap-3">
          <Button variant="secondary" onClick={() => fileInputRef.current?.click()}>
            파일 선택
          </Button>
          <span className="text-sm text-gray-600 truncate">
            {selectedFile ? selectedFile.name : '선택된 파일 없음'}
          </span>
        </div>

        <div className="mt-4">
          <Button
            onClick={() => selectedFile && importMutation.mutate(selectedFile)}
            disabled={!selectedFile || importMutation.isPending}
          >
            <Upload className="w-4 h-4 mr-2" />
            {importMutation.isPending ? '가져오는 중...' : '가져오기'}
          </Button>
        </div>

        {importMutation.isError && (
          <p className="mt-4 text-sm text-red-600">{getErrorMessage(importMutation.error)}</p>
        )}
      </div>

      {result && (
        <div className="bg-white rounded-lg border border-emerald-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <h2 className="font-semibold text-gray-900">가져오기 완료</h2>
          </div>
          <dl className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm">
            {RESULT_LABELS.map(({ key, label }) => (
              <div key={key} className="flex justify-between">
                <dt className="text-gray-500">{label}</dt>
                <dd className="font-medium text-gray-900">{result[key]}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </div>
  )
}
