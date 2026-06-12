'use client'

import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiClient, getErrorMessage } from '@/lib/api/client'
import { Button } from '@/components/ui/Button'
import {
  Table2,
  Download,
  Upload,
  FileSpreadsheet,
  ArrowLeftRight,
  CheckCircle2,
} from 'lucide-react'

interface RdpRow {
  date: string | null
  project: string | null
  pattern_code: string | null
  plate: string | null
  layer: string | null
  batch_no: string | null
  is_base: number | null
  mt: number | null
  bk: number | null
  wh: number | null
  ye: number | null
  rd: number | null
  cl: number | null
  ye_d: number | null
  thinner_pct: number | null
  hardener_pct: number | null
  result: string | null
  change_summary: string | null
  target_L: number | null
  target_a: number | null
  target_b: number | null
  measured_L: number | null
  measured_a: number | null
  measured_b: number | null
  delta_e: number | null
}

interface RdpRowsResponse {
  total: number
  projects: string[]
  rows: RdpRow[]
}

interface UpsertResult {
  path: string
  total_rows: number
  inserted: number
  updated: number
  unchanged: number
  errors?: string[]
  skipped_layers?: number
  columns_added?: string[]
}

const num = (v: number | null) => (v === null || v === undefined ? '' : v)

function ResultBanner({ title, result }: { title: string; result: UpsertResult }) {
  return (
    <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-sm">
      <div className="flex items-center gap-2 font-medium text-emerald-800 mb-1">
        <CheckCircle2 className="w-4 h-4" />
        {title}
      </div>
      <p className="text-emerald-700">
        전체 {result.total_rows}행 — 추가 {result.inserted} / 갱신 {result.updated} / 변경 없음{' '}
        {result.unchanged}
        {result.skipped_layers ? ` / RDP 출신 아님(건너뜀) ${result.skipped_layers}` : ''}
      </p>
      {result.columns_added && result.columns_added.length > 0 && (
        <p className="text-emerald-700 mt-1">
          rdp.db에 새 컬럼 추가됨: {result.columns_added.join(', ')}
        </p>
      )}
      {result.errors && result.errors.length > 0 && (
        <ul className="mt-2 text-red-600 list-disc pl-5">
          {result.errors.slice(0, 10).map(e => (
            <li key={e}>{e}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function RdpPage() {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [project, setProject] = useState('')
  const [uploadResult, setUploadResult] = useState<UpsertResult | null>(null)
  const [syncResult, setSyncResult] = useState<UpsertResult | null>(null)

  const rowsQuery = useQuery({
    queryKey: ['rdp-rows', project],
    queryFn: () =>
      apiClient.get<RdpRowsResponse>(
        `/api/rdp/rows${project ? `?project=${encodeURIComponent(project)}` : ''}`,
      ),
    retry: false,
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => apiClient.postFile<UpsertResult>('/api/rdp/excel/upload', file),
    onSuccess: result => {
      setUploadResult(result)
      setSyncResult(null)
      queryClient.invalidateQueries({ queryKey: ['rdp-rows'] })
    },
  })

  const syncMutation = useMutation({
    mutationFn: () => apiClient.post<UpsertResult>('/api/rdp/sync-back', {}),
    onSuccess: result => {
      setSyncResult(result)
      setUploadResult(null)
      queryClient.invalidateQueries({ queryKey: ['rdp-rows'] })
    },
  })

  const rows = rowsQuery.data?.rows ?? []

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-2">
        <Table2 className="w-7 h-7 text-primary-600" />
        <h1 className="text-3xl font-bold text-gray-900">RDP-DB</h1>
      </div>
      <p className="text-gray-600 mb-6">
        로컬 rdp.db의 배합 데이터를 한눈에 보고, 엑셀로 대량 수정·입력하거나 PCCS2 수정분을
        역반영합니다.
      </p>

      <div className="flex flex-wrap gap-2 mb-4">
        <a href={`${apiClient.baseUrl}/api/rdp/excel/template`} download>
          <Button variant="outline">
            <FileSpreadsheet className="w-4 h-4 mr-1.5" />
            엑셀 양식 다운로드
          </Button>
        </a>
        <a href={`${apiClient.baseUrl}/api/rdp/excel/export`} download>
          <Button variant="outline">
            <Download className="w-4 h-4 mr-1.5" />
            현재 RDP-DB 내보내기
          </Button>
        </a>
        <a href={`${apiClient.baseUrl}/api/rdp/excel/export-pccs2`} download>
          <Button variant="outline">
            <Download className="w-4 h-4 mr-1.5" />
            PCCS2 데이터 내보내기
          </Button>
        </a>
        <Button onClick={() => fileInputRef.current?.click()} disabled={uploadMutation.isPending}>
          <Upload className="w-4 h-4 mr-1.5" />
          {uploadMutation.isPending ? '업로드 중...' : '엑셀 업로드 → RDP-DB'}
        </Button>
        <Button
          variant="outline"
          disabled={syncMutation.isPending}
          onClick={() => {
            if (
              window.confirm(
                'PCCS2에서 수정한 RDP 출신 샘플들을 rdp.db에 반영합니다.\n값이 있는 컬럼만 갱신되며, 원본 파일이 직접 수정됩니다. 계속할까요?',
              )
            ) {
              syncMutation.mutate()
            }
          }}
        >
          <ArrowLeftRight className="w-4 h-4 mr-1.5" />
          {syncMutation.isPending ? '반영 중...' : 'PCCS2 → RDP-DB 반영'}
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx"
          className="hidden"
          onChange={e => {
            const file = e.target.files?.[0]
            if (file) uploadMutation.mutate(file)
            e.target.value = ''
          }}
        />
      </div>

      <div className="space-y-3 mb-6">
        {uploadMutation.isError && (
          <p className="text-sm text-red-600">{getErrorMessage(uploadMutation.error)}</p>
        )}
        {syncMutation.isError && (
          <p className="text-sm text-red-600">{getErrorMessage(syncMutation.error)}</p>
        )}
        {uploadResult && <ResultBanner title="엑셀 업로드 완료" result={uploadResult} />}
        {syncResult && <ResultBanner title="PCCS2 → RDP-DB 반영 완료" result={syncResult} />}
        {(uploadResult || syncResult) && (
          <p className="text-sm text-gray-500">
            변경된 데이터를 PCCS2에 다시 가져오려면 RDP 가져오기 페이지에서 가져오기를 실행하세요.
          </p>
        )}
      </div>

      {rowsQuery.isError && (
        <div className="p-6 text-center bg-white rounded-lg border border-gray-200">
          <p className="text-red-600 mb-3">{getErrorMessage(rowsQuery.error)}</p>
          <Button variant="outline" onClick={() => rowsQuery.refetch()}>
            다시 시도
          </Button>
        </div>
      )}

      {rowsQuery.data && (
        <>
          <div className="flex items-center gap-3 mb-3">
            <select
              value={project}
              onChange={e => setProject(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-1.5 text-sm bg-white"
            >
              <option value="">전체 프로젝트</option>
              {rowsQuery.data.projects.map(p => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
            <span className="text-sm text-gray-500">{rowsQuery.data.total}행</span>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 overflow-x-auto">
            <table className="text-xs whitespace-nowrap min-w-full">
              <thead className="bg-gray-50 text-gray-500 uppercase tracking-wide">
                <tr>
                  {[
                    '작업일', '프로젝트', '패턴', '동판', '도수', '배합', '기준',
                    'MT', 'BK', 'WH', 'YE', 'RD', 'CL', 'YE_D',
                    '신너%', '경화제%', '결과', '변경',
                    '목표 L', 'a', 'b', '측정 L', 'a', 'b', 'ΔE',
                  ].map((h, i) => (
                    <th key={i} className="px-2 py-2 text-left font-semibold">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {rows.map((r, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-2 py-1.5">{r.date}</td>
                    <td className="px-2 py-1.5 font-medium">{r.project}</td>
                    <td className="px-2 py-1.5">{r.pattern_code}</td>
                    <td className="px-2 py-1.5">{r.plate}</td>
                    <td className="px-2 py-1.5">{r.layer}</td>
                    <td className="px-2 py-1.5">{r.batch_no}</td>
                    <td className="px-2 py-1.5">{r.is_base ? '★' : ''}</td>
                    <td className="px-2 py-1.5 text-right">{num(r.mt)}</td>
                    <td className="px-2 py-1.5 text-right">{num(r.bk)}</td>
                    <td className="px-2 py-1.5 text-right">{num(r.wh)}</td>
                    <td className="px-2 py-1.5 text-right">{num(r.ye)}</td>
                    <td className="px-2 py-1.5 text-right">{num(r.rd)}</td>
                    <td className="px-2 py-1.5 text-right">{num(r.cl)}</td>
                    <td className="px-2 py-1.5 text-right">{num(r.ye_d)}</td>
                    <td className="px-2 py-1.5 text-right">{num(r.thinner_pct)}</td>
                    <td className="px-2 py-1.5 text-right">{num(r.hardener_pct)}</td>
                    <td className="px-2 py-1.5">{r.result}</td>
                    <td className="px-2 py-1.5 max-w-[160px] truncate" title={r.change_summary ?? ''}>
                      {r.change_summary}
                    </td>
                    <td className="px-2 py-1.5 text-right">{num(r.target_L)}</td>
                    <td className="px-2 py-1.5 text-right">{num(r.target_a)}</td>
                    <td className="px-2 py-1.5 text-right">{num(r.target_b)}</td>
                    <td className="px-2 py-1.5 text-right">{num(r.measured_L)}</td>
                    <td className="px-2 py-1.5 text-right">{num(r.measured_a)}</td>
                    <td className="px-2 py-1.5 text-right">{num(r.measured_b)}</td>
                    <td className="px-2 py-1.5 text-right font-medium">{num(r.delta_e)}</td>
                  </tr>
                ))}
                {rows.length === 0 && (
                  <tr>
                    <td colSpan={25} className="px-4 py-8 text-center text-gray-400">
                      데이터가 없습니다
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
