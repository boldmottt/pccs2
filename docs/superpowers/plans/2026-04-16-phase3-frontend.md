# Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build Next.js 16 + React 19 frontend with layer-by-layer recipe editor, color visualization, and API integration

**Architecture:** Client-side rendering with TanStack Query for server state, Zod for schema validation

**Tech Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS 4, TanStack Query, Lucide React

---

## Phase 3A: Project Setup

### Task 3.1: Initialize Next.js Project

**Files:**
- Create: `frontend/` structure
- Config: `next.config.js`, `tailwind.config.ts`, `tsconfig.json`

- [ ] **Step 1:** Create Next.js 16 project with TypeScript

```bash
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
```

- [ ] **Step 2:** Install additional dependencies

```bash
cd frontend
npm install lucide-react  # Icons
npm install @tanstack/react-query  # Server state
npm install zod  # Schema validation
npm install recharts  # Visualization
npm install clsx tailwind-merge  # Class utilities
```

- [ ] **Step 3:** Configure Tailwind

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss"

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Brand colors
        primary: { 50: '#f0f9ff', 500: '#0ea5e9', 600: '#0284c7' },
        // Color system
        color: {
          base: '#fafafa',
          ink: {
            red: '#ef4444',
            yellow: '#eab308',
            blue: '#3b82f6',
            green: '#22c55e',
          }
        }
      }
    }
  },
  plugins: []
}
export default config
```

- [ ] **Step 4:** Create base layout and typography

```tsx
// src/app/layout.tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gray-50 text-gray-900">
        {children}
      </body>
    </html>
  )
}
```

- [ ] **Step 5:** Commit

```bash
git add frontend/
git commit -m "chore: initialize Next.js frontend"
```

---

## Phase 3B: Type Definitions

### Task 3.2: Create Shared TypeScript Types

**Files:**
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/lib/types/project.ts`
- Create: `frontend/src/lib/types/color.ts`

- [ ] **Step 1:** Define color types

```typescript
// src/lib/types/color.ts
export interface ColorXYZ {
  L: number
  a: number
  b: number
}

export interface ColorWithDelta {
  L: number
  a: number
  b: number
  deltaE?: number
}

export interface ColorMeasurement {
  sci: ColorXYZ
  sce: ColorXYZ
  deltaESciSce?: number
}
```

- [ ] **Step 2:** Define domain types

```typescript
// src/lib/types/project.ts
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
  totalPrintLayers: number  // 총 인쇄 도수
  targetBaseColorSci: ColorXYZ
  targetBaseColorSce: ColorXYZ
}

export interface Round {
  roundId: string
  patternId: string
  workDate: string  // ISO date
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
```

- [ ] **Step 3:** Define API response types

```typescript
// src/lib/types/api.ts
import { ColorXYZ, Layer } from './project'

export interface PredictResponse {
  kmPrediction: ColorXYZ
  mlCorrection: ColorXYZ | null
  mlConfidence: number
  finalPrediction: ColorXYZ
  deltaE: number
}

export interface PredictionRequest {
  recipe: {
    layers: Layer[]
    thinnerAmount?: number
    hardenerAmount?: number
  }
  baseColor: ColorXYZ
}
```

- [ ] **Step 4:** Commit

```bash
git add frontend/src/types/
git commit -m "feat: add TypeScript type definitions"
```

---

## Phase 3C: API Integration

### Task 3.3: Create API Client

**Files:**
- Create: `frontend/src/lib/api/client.ts`
- Create: `frontend/src/lib/api/projects.ts`
- Create: `frontend/src/lib/api/patterns.ts`
- Create: `frontend/src/lib/api/samples.ts`
- Create: `frontend/src/lib/api/predict.ts`

- [ ] **Step 1:** Create API client with TanStack Query

```typescript
// src/lib/api/client.ts
import { QueryClient } from '@tanstack/react-query'

export const apiClient = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  
  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${apiClient.baseUrl}${endpoint}`)
    if (!response.ok) throw new Error(`API error: ${response.status}`)
    return response.json()
  },
  
  async post<T>(endpoint: string, data: unknown): Promise<T> {
    const response = await fetch(`${apiClient.baseUrl}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) throw new Error(`API error: ${response.status}`)
    return response.json()
  },
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})
```

- [ ] **Step 2:** Create API functions for each resource

```typescript
// src/lib/api/projects.ts
import { apiClient } from './client'
import type { Project } from '@/lib/types/project'

export const projectsApi = {
  getAll: () => apiClient.get<Project[]>('/api/projects'),
  
  getById: (id: string) => 
    apiClient.get<Project>(`/api/projects/${id}`),
  
  create: (data: Partial<Project>) =>
    apiClient.post<Project>('/api/projects', data),
  
  update: (id: string, data: Partial<Project>) =>
    apiClient.put<Project>(`/api/projects/${id}`, data),
  
  delete: (id: string) =>
    apiClient.delete(`/api/projects/${id}`),
}
```

- [ ] **Step 3:** Create predict API

```typescript
// src/lib/api/predict.ts
import { apiClient } from './client'
import type { PredictRequest, PredictResponse } from '@/lib/types/api'

export const predictApi = {
  predict: (request: PredictRequest) =>
    apiClient.post<PredictResponse>('/api/predict', request),
  
  train: (historicalData: unknown[]) =>
    apiClient.post<{ status: string }>('/api/predict/train', historicalData),
  
  health: () => apiClient.get<{ status: string }>('/api/predict/health'),
}
```

- [ ] **Step 4:** Commit

```bash
git add frontend/src/lib/api/
git commit -m "feat: add API client with TanStack Query"
```

---

## Phase 3D: Core Components

### Task 3.4: Create Reusable UI Components

**Files:**
- Create: `frontend/src/components/ui/Button.tsx`
- Create: `frontend/src/components/ui/Input.tsx`
- Create: `frontend/src/components/ui/Card.tsx`
- Create: `frontend/src/components/color/ColorSwatch.tsx`
- Create: `frontend/src/components/color/ColorComparison.tsx`

- [ ] **Step 1:** Create Button component

```tsx
// src/components/ui/Button.tsx
import { cn } from '@/lib/utils'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline'
  size?: 'sm' | 'md' | 'lg'
}

export function Button({ 
  className, 
  variant = 'primary', 
  size = 'md',
  ...props 
}: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded-lg font-medium transition-colors',
        'focus:outline-none focus:ring-2 focus:ring-offset-2',
        variant === 'primary' && 'bg-primary-600 text-white hover:bg-primary-700',
        variant === 'secondary' && 'bg-gray-200 text-gray-900 hover:bg-gray-300',
        variant === 'outline' && 'border border-gray-300 bg-transparent hover:bg-gray-100',
        size === 'sm' && 'px-3 py-1.5 text-sm',
        size === 'md' && 'px-4 py-2 text-base',
        size === 'lg' && 'px-6 py-3 text-lg',
        className
      )}
      {...props}
    />
  )
}
```

- [ ] **Step 2:** Create ColorSwatch component

```tsx
// src/components/color/ColorSwatch.tsx
import { ColorXYZ } from '@/lib/types/color'

interface ColorSwatchProps {
  color: ColorXYZ
  label?: string
  size?: 'sm' | 'md' | 'lg'
}

export function ColorSwatch({ color, label, size = 'md' }: ColorSwatchProps) {
  // Convert CIELAB to RGB for display
  const rgb = convertLabToRgb(color.L, color.a, color.b)
  const backgroundColor = `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})`
  
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16'
  }
  
  return (
    <div className="flex flex-col items-center gap-1">
      <div 
        className={cn(
          'rounded-lg shadow-md border border-gray-200',
          sizeClasses[size]
        )}
        style={{ backgroundColor }}
      />
      {label && <span className="text-xs text-gray-600">{label}</span>}
    </div>
  )
}
```

- [ ] **Step 3:** Create ColorComparison component

```tsx
// src/components/color/ColorComparison.tsx
import { ColorSwatch } from './ColorSwatch'
import { ColorXYZ } from '@/lib/types/color'

interface ColorComparisonProps {
  color1: ColorXYZ
  color2: ColorXYZ
  label1?: string
  label2?: string
  deltaE?: number
}

export function ColorComparison({ 
  color1, 
  color2, 
  label1 = 'Target', 
  label2 = 'Sample',
  deltaE 
}: ColorComparisonProps) {
  return (
    <div className="flex items-center gap-4">
      <ColorSwatch color={color1} label={label1} />
      <div className="flex flex-col items-center">
        <span className="text-sm font-medium">ΔE = {deltaE?.toFixed(2)}</span>
        {deltaE && (
          <span className={`text-xs ${deltaE < 2 ? 'text-green-600' : 'text-orange-600'}`}>
            {deltaE < 2 ? 'Acceptable' : 'Outside tolerance'}
          </span>
        )}
      </div>
      <ColorSwatch color={color2} label={label2} />
    </div>
  )
}
```

- [ ] **Step 4:** Commit

```bash
git add frontend/src/components/
git commit -m "feat: add reusable UI components"
```

---

## Phase 3E: Page Implementation

### Task 3.6: Create Project List Page

**Files:**
- Create: `frontend/src/app/projects/page.tsx`
- Create: `frontend/src/components/projects/ProjectList.tsx`
- Create: `frontend/src/components/projects/ProjectCard.tsx`

- [ ] **Step 1:** Create ProjectCard

```tsx
// src/components/projects/ProjectCard.tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Project } from '@/lib/types/project'
import { useRouter } from 'next/navigation'

interface ProjectCardProps {
  project: Project
}

export function ProjectCard({ project }: ProjectCardProps) {
  const router = useRouter()
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>{project.projectName}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            project.status === 'IN_PROGRESS' ? 'bg-blue-100 text-blue-800' :
            project.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {project.status}
          </span>
          <Button variant="outline" onClick={() => router.push(`/projects/${project.projectId}`)}>
            View Details
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
```

- [ ] **Step 2:** Create ProjectList

```tsx
// src/components/projects/ProjectList.tsx
'use client'

import { useQuery } from '@tanstack/react-query'
import { projectsApi } from '@/lib/api/projects'
import { ProjectCard } from './ProjectCard'

export function ProjectList() {
  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.getAll,
  })
  
  if (isLoading) return <div>Loading projects...</div>
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {projects?.map(project => (
        <ProjectCard key={project.projectId} project={project} />
      ))}
    </div>
  )
}
```

- [ ] **Step 3:** Create page

```tsx
// src/app/projects/page.tsx
import { ProjectList } from '@/components/projects/ProjectList'

export default function ProjectsPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Projects</h1>
        {/* TODO: Add Create Project button */}
      </div>
      <ProjectList />
    </div>
  )
}
```

- [ ] **Step 4:** Commit

```bash
git add frontend/src/app/projects/
git commit -m "feat: add projects list page"
```

### Task 3.7: Create Sample Editor with Layer-by-Layer Recipe

**Files:**
- Create: `frontend/src/app/samples/[id]/page.tsx`
- Create: `frontend/src/components/samples/SampleEditor.tsx`
- Create: `frontend/src/components/samples/LayerEditor.tsx`
- Create: `frontend/src/components/samples/InkSelector.tsx`
- Create: `frontend/src/components/samples/ColorPreview.tsx`

- [ ] **Step 1:** Create InkSelector

```tsx
// src/components/samples/InkSelector.tsx
'use client'

import { useState } from 'react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select'

interface Ink {
  inkId: string
  inkName: string
  category: string
}

interface InkSelectorProps {
  inks: Ink[]
  onSelect: (ink: Ink, amount: number) => void
}

export function InkSelector({ inks, onSelect }: InkSelectorProps) {
  const [selectedInk, setSelectedInk] = useState<string>('')
  const [amount, setAmount] = useState<number>(10)
  
  const handleAdd = () => {
    const ink = inks.find(i => i.inkId === selectedInk)
    if (ink) onSelect(ink, amount)
  }
  
  return (
    <div className="flex gap-2">
      <Select 
        value={selectedInk} 
        onValueChange={setSelectedInk}
      >
        <SelectTrigger>
          <SelectValue placeholder="Select ink" />
        </SelectTrigger>
        <SelectContent>
          {inks.map(ink => (
            <SelectItem key={ink.inkId} value={ink.inkId}>
              {ink.inkName}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <input
        type="number"
        value={amount}
        onChange={e => setAmount(Number(e.target.value))}
        className="w-20 px-3 py-2 border rounded-lg"
        min="0"
      />
      <Button onClick={handleAdd}>Add</Button>
    </div>
  )
}
```

- [ ] **Step 2:** Create LayerEditor

```tsx
// src/components/samples/LayerEditor.tsx
'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { InkItem } from '@/lib/types/project'

interface LayerEditorProps {
  layerNumber: number
  inkItems: InkItem[]
  onInksChange: (items: InkItem[]) => void
  onThinnerChange: (value: number) => void
  onHardenerChange: (value: number) => void
}

export function LayerEditor({
  layerNumber,
  inkItems,
  onInksChange,
  onThinnerChange,
  onHardenerChange,
}: LayerEditorProps) {
  const [selectedInk, setSelectedInk] = useState('')
  const [amount, setAmount] = useState(10)
  
  const handleAddInk = () => {
    onInksChange([...inkItems, { inkId: selectedInk, amount }])
    setSelectedInk('')
    setAmount(10)
  }
  
  const handleRemoveInk = (index: number) => {
    onInksChange(inkItems.filter((_, i) => i !== index))
  }
  
  return (
    <Card>
      <div className="p-4">
        <h3 className="text-lg font-semibold mb-4">Layer {layerNumber}</h3>
        
        <div className="flex gap-2 mb-4">
          <Select value={selectedInk} onValueChange={setSelectedInk}>
            <SelectTrigger><SelectValue placeholder="Select ink" /></SelectTrigger>
            <SelectContent>
              {/* Populate with inks */}
            </SelectContent>
          </Select>
          <input
            type="number"
            value={amount}
            onChange={e => setAmount(Number(e.target.value))}
            className="w-20 px-3 py-2 border rounded"
          />
          <Button onClick={handleAddInk}>Add</Button>
        </div>
        
        <div className="space-y-2 mb-4">
          {inkItems.map((item, index) => (
            <div key={index} className="flex items-center gap-2">
              <span>{item.inkId}: {item.amount}g</span>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => handleRemoveInk(index)}
              >
                Remove
              </Button>
            </div>
          ))}
        </div>
        
        <div className="flex gap-4">
          <label>
            Thinner (%):
            <input
              type="number"
              value=""
              onChange={e => onThinnerChange(Number(e.target.value))}
              className="ml-2 w-20 px-3 py-1 border rounded"
            />
          </label>
          <label>
            Hardener (%):
            <input
              type="number"
              value=""
              onChange={e => onHardenerChange(Number(e.target.value))}
              className="ml-2 w-20 px-3 py-1 border rounded"
            />
          </label>
        </div>
      </div>
    </Card>
  )
}
```

- [ ] **Step 3:** Create SampleEditor

```tsx
// src/components/samples/SampleEditor.tsx
'use client'

import { useState } from 'react'
import { LayerEditor } from './LayerEditor'
import { ColorPreview } from './ColorPreview'
import { InkItem, Layer } from '@/lib/types/project'

interface SampleEditorProps {
  initialLayers?: Layer[]
  onSave: (layers: Layer[]) => void
}

export function SampleEditor({ initialLayers = [], onSave }: SampleEditorProps) {
  const [layers, setLayers] = useState<Layer[]>(initialLayers)
  
  const addLayer = () => {
    const newLayerNumber = layers.length + 1
    setLayers([...layers, {
      layerNumber: newLayerNumber,
      inkItems: [],
      printColorSci: { L: 0, a: 0, b: 0 },
      printColorSce: { L: 0, a: 0, b: 0 }
    }])
  }
  
  const updateLayer = (layerNumber: number, updates: Partial<Layer>) => {
    setLayers(layers.map(l => 
      l.layerNumber === layerNumber ? { ...l, ...updates } : l
    ))
  }
  
  const handleInksChange = (layerNumber: number, inkItems: InkItem[]) => {
    updateLayer(layerNumber, { inkItems })
  }
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">Recipe Layers</h2>
        <Button onClick={addLayer}>Add Layer</Button>
      </div>
      
      {layers.map(layer => (
        <LayerEditor
          key={layer.layerNumber}
          layerNumber={layer.layerNumber}
          inkItems={layer.inkItems}
          onInksChange={(items) => handleInksChange(layer.layerNumber, items)}
          onThinnerChange={(v) => updateLayer(layer.layerNumber, { thinnerPct: v })}
          onHardenerChange={(v) => updateLayer(layer.layerNumber, { hardenerPct: v })}
        />
      ))}
      
      <ColorPreview 
        layers={layers} 
        baseColor={{ L: 100, a: 0, b: 0 }}
        onPredict={(prediction) => {
          // Update print colors with prediction
          const updatedLayers = layers.map((l, i) => ({
            ...l,
            printColorSci: prediction.finalPrediction,
            printColorSce: prediction.finalPrediction
          }))
          setLayers(updatedLayers)
        }}
      />
      
      <Button onClick={() => onSave(layers)}>Save Sample</Button>
    </div>
  )
}
```

- [ ] **Step 4:** Create ColorPreview

```tsx
// src/components/samples/ColorPreview.tsx
'use client'

import { useState } from 'react'
import { predictApi } from '@/lib/api/predict'
import { Layer, ColorXYZ } from '@/lib/types/project'
import { ColorComparison } from '@/components/color/ColorComparison'

interface ColorPreviewProps {
  layers: Layer[]
  baseColor: ColorXYZ
  onPredict: (prediction: unknown) => void
}

export function ColorPreview({ layers, baseColor, onPredict }: ColorPreviewProps) {
  const [prediction, setPrediction] = useState<unknown>(null)
  const [isLoading, setIsLoading] = useState(false)
  
  const handlePredict = async () => {
    setIsLoading(true)
    try {
      const result = await predictApi.predict({
        recipe: { layers },
        baseColor
      })
      setPrediction(result)
      onPredict(result)
    } finally {
      setIsLoading(false)
    }
  }
  
  return (
    <div className="border-t pt-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Color Prediction</h3>
        <button 
          onClick={handlePredict}
          disabled={isLoading || layers.some(l => l.inkItems.length === 0)}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg disabled:opacity-50"
        >
          {isLoading ? 'Predicting...' : 'Predict Color'}
        </button>
      </div>
      
      {prediction && (
        <ColorComparison
          color1={baseColor}
          color2={prediction.finalPrediction as ColorXYZ}
          label1="Base"
          label2="Predicted"
          deltaE={(prediction.deltaE as number)}
        />
      )}
    </div>
  )
}
```

- [ ] **Step 5:** Create sample page

```tsx
// src/app/samples/[id]/page.tsx
'use client'

import { SampleEditor } from '@/components/samples/SampleEditor'

interface SamplePageProps {
  params: { id: string }
}

export default function SamplePage({ params }: SamplePageProps) {
  const handleSave = async (layers: unknown[]) => {
    // TODO: Save to API
    console.log('Saving sample:', layers)
  }
  
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Sample Editor</h1>
      <SampleEditor onSave={handleSave} />
    </div>
  )
}
```

- [ ] **Step 6:** Commit

```bash
git add frontend/src/app/samples/ frontend/src/components/samples/
git commit -m "feat: add sample editor with layer-by-layer recipe"
```

---

## Phase 3F: Visualization

### Task 3.8: Add Blend Visualization Components

**Files:**
- Create: `frontend/src/components/visualization/InkDonutChart.tsx`
- Create: `frontend/src/components/visualization/ColorTrendChart.tsx`

- [ ] **Step 1:** Create InkDonutChart

```tsx
// src/components/visualization/InkDonutChart.tsx
'use client'

import { PieChart, Pie, Cell, Tooltip, Legend } from 'recharts'
import { InkItem } from '@/lib/types/project'

const COLOR_PALETTE = [
  '#ef4444', '#eab308', '#3b82f6', '#22c55e', 
  '#a855f7', '#ec4899', '#14b8a6', '#f97316'
]

interface InkDonutChartProps {
  inkItems: InkItem[]
  totalAmount: number
}

export function InkDonutChart({ inkItems, totalAmount }: InkDonutChartProps) {
  const data = inkItems.map((item, index) => ({
    name: item.inkId,
    value: item.amount,
    percentage: totalAmount > 0 ? (item.amount / totalAmount * 100).toFixed(1) : 0
  }))
  
  return (
    <div className="flex items-center gap-4">
      <PieChart width={200} height={200}>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={80}
          fill="#8884d8"
          dataKey="value"
          label={(entry) => `${entry.name}: ${entry.percentage}%`}
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLOR_PALETTE[index % COLOR_PALETTE.length]} />
          ))}
        </Pie>
        <Tooltip />
      </PieChart>
      <div className="space-y-2">
        {data.map((entry, index) => (
          <div key={entry.name} className="flex items-center gap-2">
            <div 
              className="w-4 h-4 rounded" 
              style={{ backgroundColor: COLOR_PALETTE[index % COLOR_PALETTE.length] }}
            />
            <span className="text-sm">{entry.name}: {entry.value}g</span>
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2:** Create ColorTrendChart

```tsx
// src/components/visualization/ColorTrendChart.tsx
'use client'

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts'
import { ColorXYZ } from '@/lib/types/color'

interface DataPoint {
  round: string
  L: number
  a: number
  b: number
}

interface ColorTrendChartProps {
  dataPoints: DataPoint[]
  targetColor: ColorXYZ
}

export function ColorTrendChart({ dataPoints, targetColor }: ColorTrendChartProps) {
  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Color Trend Over Rounds</h3>
      <LineChart width={600} height={300} data={dataPoints}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="round" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="L" stroke="#8884d8" name="L" />
        <Line type="monotone" dataKey="a" stroke="#82ca9d" name="a" />
        <Line type="monotone" dataKey="b" stroke="#ffc658" name="b" />
        {/* Target lines */}
        <Line 
          type="monotone" 
          dataKey={() => targetColor.L} 
          stroke="#ff7300" 
          name="Target L" 
          strokeDasharray="5 5"
        />
        <Line 
          type="monotone" 
          dataKey={() => targetColor.a} 
          stroke="#ff7300" 
          name="Target a" 
          strokeDasharray="5 5"
        />
        <Line 
          type="monotone" 
          dataKey={() => targetColor.b} 
          stroke="#ff7300" 
          name="Target b" 
          strokeDasharray="5 5"
        />
      </LineChart>
    </div>
  )
}
```

- [ ] **Step 3:** Integrate into sample page

```tsx
// Add to Sample page
import { InkDonutChart } from '@/components/visualization/InkDonutChart'

// In the page component
{layers.map(layer => (
  <div key={layer.layerNumber}>
    <h4 className="font-semibold">Layer {layer.layerNumber}</h4>
    <InkDonutChart 
      inkItems={layer.inkItems} 
      totalAmount={layer.inkItems.reduce((sum, item) => sum + item.amount, 0)} 
    />
  </div>
))}
```

- [ ] **Step 4:** Commit

```bash
git add frontend/src/components/visualization/
git commit -m "feat: add blend visualization components"
```

---

## Testing Requirements

- All pages should load without errors
- Color prediction API integration should work
- All components should have hover/focus states
- Responsive design at 320, 768, 1024, 1440px

---

**Plan complete. Ready to execute.**

**Execution options:**
1. **Subagent-Driven** (recommended) - Dispatch subagent per task
2. **Inline Execution** - Execute tasks in this session

Which approach?
