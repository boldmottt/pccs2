import { apiClient } from './client'
import type { Sample, SampleCreate, SampleUpdate } from '@/lib/types/project'

export interface CopyLayerRequest {
  source_sample_id: string
  source_layer_number: number
  target_layer_number: number
}

export const samplesApi = {
  list: (params?: { round_id?: string; pattern_id?: string }) => {
    const searchParams = new URLSearchParams()
    if (params?.round_id) searchParams.set('round_id', params.round_id)
    if (params?.pattern_id) searchParams.set('pattern_id', params.pattern_id)
    const query = searchParams.toString()
    return apiClient.get<Sample[]>(`/api/samples/${query ? `?${query}` : ''}`)
  },

  get: (sampleId: string) => apiClient.get<Sample>(`/api/samples/${sampleId}`),

  /** sample_number는 백엔드에서 자동 부여 */
  create: (roundId: string, data: SampleCreate) =>
    apiClient.post<Sample>(`/api/samples/round/${roundId}`, data),

  update: (sampleId: string, data: SampleUpdate) =>
    apiClient.put<Sample>(`/api/samples/${sampleId}`, data),

  remove: (sampleId: string) => apiClient.delete<void>(`/api/samples/${sampleId}`),

  /** 다른 샘플의 레이어 배합비를 이 샘플로 복사 → 갱신된 샘플 반환 */
  copyLayer: (sampleId: string, data: CopyLayerRequest) =>
    apiClient.post<Sample>(`/api/samples/${sampleId}/copy-layer`, data),
}
