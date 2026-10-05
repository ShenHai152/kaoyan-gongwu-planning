// Pure projection: API response -> view model. No side effects, no fetching.
import type { ReachMatchSafetyResponse } from '@/api/client'

export type Band = 'reach' | 'match' | 'safety'

export interface YearLineView {
  year: number
  totalScore: number
  department: string | null
}

export interface SchoolRowView {
  school: string
  band: Band
  referenceLine: number
  margin: number
  yearsObserved: number
  department: string | null
  region: string | null
  zone: string | null
  is985: boolean
  is211: boolean
  isSelfDrawn: boolean
  lines: YearLineView[]
}

export interface ReachMatchViewModel {
  yearTo: number | null
  window: number
  score: number
  bands: Record<Band, SchoolRowView[]>
  counts: Record<Band, number>
  total: number
  coverageWarning: string | null
  disclaimer: string
  isEmpty: boolean
}

const BAND_ORDER: Band[] = ['reach', 'match', 'safety']

function asBand(value: string): Band {
  return (BAND_ORDER as string[]).includes(value) ? (value as Band) : 'match'
}

export function projectReachMatchSafety(
  response: ReachMatchSafetyResponse,
): ReachMatchViewModel {
  const bands: Record<Band, SchoolRowView[]> = { reach: [], match: [], safety: [] }
  for (const row of response.rows ?? []) {
    bands[asBand(row.band)].push({
      school: row.school_name,
      band: asBand(row.band),
      referenceLine: row.reference_line,
      margin: row.margin,
      yearsObserved: row.years_observed,
      department: row.department ?? null,
      region: row.province ?? null,
      zone: row.zone ?? null,
      is985: row.is_985,
      is211: row.is_211,
      isSelfDrawn: row.is_self_drawn,
      // The backend orders by margin; keep that order inside each band.
      lines: [...(row.lines ?? [])]
        .map((line) => ({
          year: line.year,
          totalScore: line.total_score,
          department: line.department ?? null,
        }))
        .sort((a, b) => a.year - b.year),
    })
  }
  for (const band of BAND_ORDER) {
    bands[band].sort((a, b) => a.margin - b.margin)
  }
  const total = BAND_ORDER.reduce((sum, band) => sum + bands[band].length, 0)
  return {
    yearTo: response.year_to ?? null,
    window: response.window,
    score: response.score,
    bands,
    counts: { reach: bands.reach.length, match: bands.match.length, safety: bands.safety.length },
    total,
    coverageWarning: response.coverage_warning ?? null,
    disclaimer: response.disclaimer,
    isEmpty: total === 0,
  }
}
