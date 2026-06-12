// 백엔드 API 계약 (snake_case)에 1:1 대응하는 엔티티 타입 정의
import type { Lab } from './color'

export type { Lab }

// ---------- Project ----------
export type ProjectStatus = 'IN_PROGRESS' | 'COMPLETED' | 'ON_HOLD'

export interface Project {
  project_id: string
  project_name: string
  customer?: string | null
  status: ProjectStatus
  start_date?: string | null
  target_completion?: string | null
  memo?: string | null
  created_at: string
  updated_at: string
}

export interface ProjectCreate {
  project_name: string
  customer?: string
  status?: ProjectStatus
  start_date?: string
  target_completion?: string
  memo?: string
}

// ---------- Pattern ----------
export type PatternStatus = 'DEVELOPING' | 'COMPLETED' | 'ON_HOLD'

export interface Pattern {
  pattern_id: string
  project_id: string
  pattern_name: string
  total_print_layers: number
  target_base_color_sci?: Lab | null
  target_base_color_sce?: Lab | null
  target_base_material?: string | null
  status: PatternStatus
  notes?: string | null
  approved_sample_id?: string | null
  success_rate?: number | null
  avg_delta_e?: number | null
  created_at: string
  updated_at: string
}

export interface PatternCreate {
  project_id: string
  pattern_name: string
  total_print_layers: number
  target_base_color_sci?: Lab
  target_base_color_sce?: Lab
  target_base_material?: string
  status?: PatternStatus
  notes?: string
}

// ---------- Round ----------
export interface Round {
  round_id: string
  pattern_id: string
  round_number: number
  work_date?: string | null
  operator?: string | null
  work_location?: string | null
  created_at: string
  updated_at: string
}

export interface RoundCreate {
  work_date?: string
  operator?: string
  work_location?: string
}

// ---------- Sample ----------
export type SuccessFlag = 'SUCCESS' | 'FAILED' | 'PENDING'

export interface InkItem {
  ink_id: string
  amount: number
}

export interface Layer {
  layer_number: number
  ink_items: InkItem[]
  thinner_pct?: number | null
  hardener_pct?: number | null
  print_color_sci?: Lab | null
  print_color_sce?: Lab | null
  delta_E_from_target?: number | null
  note?: string | null
}

export interface Sample {
  sample_id: string
  round_id: string
  pattern_id: string
  sample_number: number
  base_color_sci: Lab
  base_color_sce: Lab
  base_material: string
  layers: Layer[]
  final_delta_e?: number | null
  success_flag: SuccessFlag
  success_notes?: string | null
  created_at: string
  updated_at: string
}

export interface SampleCreate {
  base_color_sci: Lab
  base_color_sce: Lab
  base_material: string
  layers: Layer[]
  success_flag?: SuccessFlag
  success_notes?: string
}

export interface SampleUpdate {
  base_color_sci?: Lab
  base_color_sce?: Lab
  base_material?: string
  layers?: Layer[]
  final_delta_e?: number
  success_flag?: SuccessFlag
  success_notes?: string
}

// ---------- Ink ----------
export type InkCategory = 'COLOR' | 'TRANSPARENT' | 'EFFECT' | 'ADDITIVE'

export interface Ink {
  ink_id: string
  ink_name: string
  ink_category: InkCategory
  manufacturer?: string | null
  is_blend_ink: boolean
  blend_recipe?: Record<string, unknown> | null
  plate_id?: string | null
  solid_color_sci?: Lab | null
  solid_color_sce?: Lab | null
  delta_sci_sce?: number | null
  gloss_index?: number | null
  gloss_GU?: number | null
  viscosity?: number | null
  density?: number | null
  memo?: string | null
  registered_at: string
  updated_at: string
}

export interface InkCreate {
  ink_name: string
  ink_category: InkCategory
  manufacturer?: string
  is_blend_ink?: boolean
  blend_recipe?: Record<string, unknown>
  plate_id?: string
  solid_color_sci?: Lab
  solid_color_sce?: Lab
  gloss_GU?: number
  viscosity?: number
  density?: number
  memo?: string
}

// ---------- Base Master ----------
export interface BaseMaster {
  base_id: string
  base_code: string
  base_name?: string | null
  material?: string | null
  color_sci?: Lab | null
  color_sce?: Lab | null
  maker?: string | null
  memo?: string | null
  created_at: string
  updated_at: string
}

export interface BaseMasterCreate {
  base_code: string
  base_name?: string
  material?: string
  color_sci?: Lab
  color_sce?: Lab
  maker?: string
  memo?: string
}

// ---------- Plate (동판) ----------
export interface Plate {
  plate_id: string
  pattern_id: string
  plate_code: string
  emboss_type?: string | null
  emboss_depth_um?: number | null
  memo?: string | null
  created_at: string
  updated_at: string
}

export interface PlateCreate {
  pattern_id: string
  plate_code: string
  emboss_type?: string
  emboss_depth_um?: number
  memo?: string
}
