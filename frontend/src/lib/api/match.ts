import { apiClient } from './client'
import type { InkItem, Lab } from '@/lib/types/project'

export interface MatchRequest {
  pattern_id: string
  target_color: Lab
  layer_number: number
  exclude_inks?: string[]
  max_components?: number
}

export interface RecommendedRecipe {
  rank: number
  recipe: InkItem[]
  suggested_thinner_ratio: number
  predicted_color: Lab
  predicted_delta_E: number
  confidence_score: number
}

export interface MatchResponse {
  result_id: string
  pattern_id: string
  recommended_recipes: RecommendedRecipe[]
  engine_used: string
  model_version: string
}

export const matchApi = {
  match: (data: MatchRequest) => apiClient.post<MatchResponse>('/api/match/', data),
}
