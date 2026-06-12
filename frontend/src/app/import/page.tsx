'use client'

import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient, getErrorMessage } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Database, Upload, CheckCircle2, FolderSearch, RefreshCw } from 'lucide-react'

interface RdpImportResult {
  projects_created: number
  patterns_created: number
  plates_created: number
  rounds_created: number
  samples_created: number
  samples_updated: number
  samples_skipped: number
  inks_created: number
  total_rows: number
}

interface RdpLocalStatus {
  path: string
  exists: boolean
  size?: number
  modified_at?: string
}

const RESULT_LABELS: Array<{ key: keyof RdpImportResult; label: string }> = [
  { key: 'total_rows', label: '전체 배합 행' },
  { key: 'projects_created', label: '프로젝트 생성' },
  { key: 'patterns_created', label: '패턴 생성' },
  { key: 'plates_created', label: '동판 생성' },
  { key: 'rounds_created', label: '라운드 생성' },
  { key: 'samples_created', label: '샘플 생성' },
  { key: 'samples_updated', label: '변경 업데이트' },
  { key: 'samples_skipped', label: '중복 건너뜀' },
  { key: 'inks_created', label: '잉크 자동 등록' },
]

function ResultCard({ result }: { result: RdpImportResult }) {
  return (
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
  )
}

const PATH_STORAGE_KEY = 'pccs2.rdpDbPath'

export default function ImportPage() {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [customPath, setCustomPath] = useState<string>(() =>
    typeof window !== 'undefined' ? (localStorage.getItem(PATH_STORAGE_KEY) ?? '') : '',
  )

  const statusQuery = useQuery({
    queryKey: ['rdp-local-status', customPath],
    queryFn: () =>
      apiClient.get<RdpLocalStatus>(
        `/api/import/rdp/local-status${customPath ? `?path=${encodeURIComponent(customPath)}` : ''}`,
      ),
  })

  const localImportMutation = useMutation({
    mutationFn: () =>
      apiClient.post<RdpImportResult>('/api/import/rdp/local', customPath ? { path: customPath } : {}),
    onSuccess: () => {
      queryClient.invalidateQueries()
    },
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => apiClient.postFile<RdpImportResult>('/api/import/rdp', file),
    onSuccess: () => {
      queryClient.invalidateQueries()
    },
  })

  const status = statusQuery.data
  const result = localImportMutation.data ?? uploadMutation.data

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-2">
        <Database className="w-7 h-7 text-blue-600" />
        <h1 className="text-2xl font-bold text-gray-900">RDP-DB 가져오기</h1>
      </div>
      <p className="text-gray-500 mb-8">
        작업일지에서 추출한 RDP 배합비 DB(<code className="text-sm bg-gray-100 px-1 rounded">rdp.db</code>)를
        프로젝트 → 패턴 → 라운드 → 샘플 계층으로 변환합니다.
        이미 가져온 배합은 자동으로 건너뛰므로 반복 실행해도 안전합니다.
      </p>

      {/* 로컬 자동 가져오기 */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <div className="flex items-center gap-2 mb-3">
          <FolderSearch className="w-5 h-5 text-primary-600" />
          <h2 className="font-semibold text-gray-900">자동 가져오기 (권장)</h2>
        </div>
        <p className="text-sm text-gray-500 mb-4">
          이 컴퓨터의 <code className="bg-gray-100 px-1 rounded">rdp.db</code>를 직접 읽습니다 — 파일 첨부가 필요 없습니다.
        </p>

        {statusQuery.isError && (
          <div className="p-3 rounded-lg border bg-red-50 border-red-200 text-sm text-red-700 mb-4">
            <p className="font-medium">백엔드에서 로컬 파일 상태를 확인하지 못했습니다.</p>
            <p className="text-xs mt-1">
              백엔드 서버가 구버전으로 실행 중일 수 있습니다 — 터미널에서 서버를 종료(Ctrl+C)하고{' '}
              <code className="bg-red-100 px-1 rounded">./start.sh</code>로 다시 시작해 주세요.
            </p>
            <p className="text-xs mt-1 text-red-500">{getErrorMessage(statusQuery.error)}</p>
          </div>
        )}

        {status && (
          <div
            className={`p-3 rounded-lg border text-sm mb-4 ${
              status.exists
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : 'bg-amber-50 border-amber-200 text-amber-800'
            }`}
          >
            {status.exists ? (
              <>
                <p className="font-medium">파일 발견 ✓</p>
                <p className="font-mono text-xs mt-1 break-all">{status.path}</p>
                <p className="text-xs mt-1">
                  {((status.size ?? 0) / 1024).toFixed(1)} KB · 마지막 수정 {status.modified_at}
                </p>
              </>
            ) : (
              <>
                <p className="font-medium">파일을 찾지 못했습니다</p>
                <p className="font-mono text-xs mt-1 break-all">{status.path}</p>
                <p className="text-xs mt-1">아래에 실제 경로를 입력하거나, 파일 업로드를 이용하세요.</p>
              </>
            )}
          </div>
        )}

        <div className="flex items-end gap-2 mb-4">
          <div className="flex-1">
            <Input
              label="rdp.db 경로 (비우면 기본 경로 사용)"
              placeholder="~/MySecondBrain/Areas/NIFCO/RDP-DB/rdp.db"
              value={customPath}
              onChange={e => {
                setCustomPath(e.target.value)
                localStorage.setItem(PATH_STORAGE_KEY, e.target.value)
              }}
            />
          </div>
          <Button variant="outline" onClick={() => statusQuery.refetch()} title="경로 다시 확인">
            <RefreshCw className={`w-4 h-4 ${statusQuery.isFetching ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        <Button
          onClick={() => localImportMutation.mutate()}
          disabled={localImportMutation.isPending || (status ? !status.exists : false)}
        >
          <Database className="w-4 h-4 mr-2" />
          {localImportMutation.isPending ? '가져오는 중...' : '지금 가져오기'}
        </Button>

        {localImportMutation.isError && (
          <p className="mt-4 text-sm text-red-600">{getErrorMessage(localImportMutation.error)}</p>
        )}
      </div>

      {/* 파일 업로드 (대안) */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <h2 className="font-semibold text-gray-900 mb-3">파일 업로드</h2>
        <input
          ref={fileInputRef}
          type="file"
          accept=".db,.sqlite,.sqlite3"
          className="hidden"
          onChange={(e) => {
            setSelectedFile(e.target.files?.[0] ?? null)
            uploadMutation.reset()
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
            variant="outline"
            onClick={() => selectedFile && uploadMutation.mutate(selectedFile)}
            disabled={!selectedFile || uploadMutation.isPending}
          >
            <Upload className="w-4 h-4 mr-2" />
            {uploadMutation.isPending ? '가져오는 중...' : '업로드로 가져오기'}
          </Button>
        </div>

        {uploadMutation.isError && (
          <p className="mt-4 text-sm text-red-600">{getErrorMessage(uploadMutation.error)}</p>
        )}
      </div>

      {result && <ResultCard result={result} />}
    </div>
  )
}
