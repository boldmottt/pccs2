export interface Project {
  projectId: string
  projectName: string
  status: 'IN_PROGRESS' | 'COMPLETED' | 'ON_HOLD'
  createdAt: string
  updatedAt: string
}

export interface Pattern {
  patternId: string
  projectId: string
  patternName: string
  totalPrintLayers: number
  targetBaseColorSci: ColorXYZ
  targetBaseColorSce: ColorXYZ
}

export interface Round {
  roundId: string
  patternId: string
  workDate: string
  operator: string
  workLocation: string
  createdAt: string
}

export interface InkItem {
  inkId: string
  amount: number
}

export interface Layer {
  layerNumber: number
  inkItems: InkItem[]
  thinnerPct?: number
  hardenerPct?: number
  printColorSci: ColorXYZ
  printColorSce: ColorXYZ
  deltaEFromTarget?: number
}

export interface Sample {
  sampleId: string
  roundId: string
  baseColorSci: ColorXYZ
  baseColorSce: ColorXYZ
  layers: Layer[]
  successFlag: 'SUCCESS' | 'FAILED' | 'PENDING'
}

export interface Ink {
  inkId: string
  inkName: string
  category: 'PRIMARY' | 'AUXILIARY' | 'TRANSPARENT' | 'HARDENER' | 'THINNER'
  isBlendInk: boolean
  solidColorSci: ColorXYZ
  solidColorSce: ColorXYZ
  blendRecipe?: Layer[]
}

export type { ColorXYZ } from './color'
