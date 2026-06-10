/** API 오류: HTTP 상태 코드 + 백엔드 detail 메시지를 담는 typed error */
export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/** ApiError → 사용자에게 보여줄 한국어 메시지 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 0) return '서버에 연결할 수 없습니다. 백엔드가 실행 중인지 확인하세요.'
    return error.message
  }
  if (error instanceof Error) return error.message
  return '알 수 없는 오류가 발생했습니다.'
}

async function parseErrorMessage(response: Response): Promise<string> {
  let message = `요청이 실패했습니다 (HTTP ${response.status})`
  try {
    const body = await response.json()
    if (body && typeof body === 'object' && 'detail' in body) {
      const detail = (body as { detail: unknown }).detail
      if (typeof detail === 'string') {
        message = detail
      } else if (detail !== undefined && detail !== null) {
        message = JSON.stringify(detail)
      }
    }
  } catch {
    // 응답 본문이 JSON이 아닌 경우 기본 메시지 사용
  }
  return message
}

async function request<T>(endpoint: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE_URL}${endpoint}`, init)
  } catch {
    throw new ApiError(0, '서버에 연결할 수 없습니다.')
  }

  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorMessage(response))
  }

  if (response.status === 204) {
    return undefined as T
  }

  const text = await response.text()
  if (!text) {
    return undefined as T
  }
  return JSON.parse(text) as T
}

export const apiClient = {
  baseUrl: BASE_URL,

  get<T>(endpoint: string): Promise<T> {
    return request<T>(endpoint)
  },

  post<T>(endpoint: string, data?: unknown): Promise<T> {
    return request<T>(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: data !== undefined ? JSON.stringify(data) : undefined,
    })
  },

  put<T>(endpoint: string, data: unknown): Promise<T> {
    return request<T>(endpoint, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
  },

  delete<T>(endpoint: string): Promise<T> {
    return request<T>(endpoint, { method: 'DELETE' })
  },
}
