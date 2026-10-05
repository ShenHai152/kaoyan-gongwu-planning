// Thin API client over the generated schema. The backend owns the contract;
// this file only adds a base URL, error normalization, and a timeout.
import type { paths } from './schema'

const BASE = ''

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

type Query = Record<string, string | number | boolean | null | undefined | string[]>

function toQueryString(query?: Query): string {
  if (!query) return ''
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value === null || value === undefined || value === '') continue
    // Repeated params carry multi-select filters (list[str] on the backend).
    if (Array.isArray(value)) {
      for (const item of value) params.append(key, String(item))
      continue
    }
    params.append(key, String(value))
  }
  const rendered = params.toString()
  return rendered ? `?${rendered}` : ''
}

async function request<T>(path: string, query?: Query): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 15000)
  try {
    const response = await fetch(`${BASE}${path}${toQueryString(query)}`, {
      signal: controller.signal,
      headers: { Accept: 'application/json' },
    })
    if (!response.ok) {
      throw new ApiError(response.status, `request failed: ${response.status}`)
    }
    return (await response.json()) as T
  } finally {
    clearTimeout(timer)
  }
}

type Json<T> = T extends { content: { 'application/json': infer R } } ? R : never

export type ReachMatchSafetyResponse = Json<
  paths['/api/kaoyan/reach-match-safety']['get']['responses']['200']
>
export type ReachMatchSafetyQuery =
  paths['/api/kaoyan/reach-match-safety']['get']['parameters']['query']
export type ProvincesResponse = Json<
  paths['/api/kaoyan/provinces']['get']['responses']['200']
>
export type ProgramSearchResponse = Json<
  paths['/api/kaoyan/programs']['get']['responses']['200']
>
export type ProgramRankingResponse = Json<
  paths['/api/kaoyan/rankings/program']['get']['responses']['200']
>
export type ProgramRankingQuery =
  paths['/api/kaoyan/rankings/program']['get']['parameters']['query']

export function fetchReachMatchSafety(
  query: ReachMatchSafetyQuery,
): Promise<ReachMatchSafetyResponse> {
  return request<ReachMatchSafetyResponse>('/api/kaoyan/reach-match-safety', query as Query)
}

export function fetchProvinces(): Promise<ProvincesResponse> {
  return request<ProvincesResponse>('/api/kaoyan/provinces')
}

export function searchPrograms(
  query: string,
  limit = 50,
): Promise<ProgramSearchResponse> {
  return request<ProgramSearchResponse>('/api/kaoyan/programs', { query, limit })
}

export function fetchProgramRanking(
  query: ProgramRankingQuery,
): Promise<ProgramRankingResponse> {
  return request<ProgramRankingResponse>('/api/kaoyan/rankings/program', query as Query)
}

export type HeatRankingResponse = Json<
  paths['/api/kaoyan/heat-ranking']['get']['responses']['200']
>
export type HeatRankingQuery =
  paths['/api/kaoyan/heat-ranking']['get']['parameters']['query']
export type AiReportResponse = Json<
  paths['/api/kaoyan/ai-report']['post']['responses']['200']
>
export type AiReportRequest =
  paths['/api/kaoyan/ai-report']['post']['requestBody']['content']['application/json']

export function fetchHeatRanking(query: HeatRankingQuery): Promise<HeatRankingResponse> {
  return request<HeatRankingResponse>('/api/kaoyan/heat-ranking', query as Query)
}

export async function requestAiReport(body: AiReportRequest): Promise<AiReportResponse> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 60000)
  try {
    const response = await fetch(`${BASE}/api/kaoyan/ai-report`, {
      method: 'POST',
      signal: controller.signal,
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(body),
    })
    if (!response.ok) {
      throw new ApiError(response.status, `request failed: ${response.status}`)
    }
    return (await response.json()) as AiReportResponse
  } finally {
    clearTimeout(timer)
  }
}
