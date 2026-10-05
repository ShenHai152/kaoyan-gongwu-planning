// Pure projection: heat ranking response -> view model. No side effects.
import type { HeatRankingResponse } from '@/api/client'

export interface HeatRowView {
  rank: number
  school: string
  college: string
  direction: string
  subjectClass: string | null
  region: string | null
  tier: string | null
  heat: number | null
  discussion: number | null
  line2026: number | null
  admitCount: number | null
  source: string
}

export interface HeatViewModel {
  sort: string
  rows: HeatRowView[]
  excludedMissing: number
  disclaimer: string
  isEmpty: boolean
}

export function projectHeatRanking(response: HeatRankingResponse): HeatViewModel {
  const rows: HeatRowView[] = (response.rows ?? []).map((row) => ({
    rank: row.rank,
    school: row.school_name,
    college: row.college,
    direction: row.direction,
    subjectClass: row.subject_class ?? null,
    region: row.region ?? null,
    tier: row.tier ?? null,
    // The sort key decides which heat figure is the headline number.
    heat: response.sort === 'comp' ? (row.heat_comp ?? null) : (row.heat_net ?? null),
    discussion: row.wd_count ?? null,
    line2026: row.line_2026_value ?? null,
    admitCount: row.admit_cnt_value ?? null,
    source: row.source_file,
  }))
  return {
    sort: response.sort,
    rows,
    excludedMissing: response.excluded_missing,
    disclaimer: response.disclaimer,
    isEmpty: rows.length === 0,
  }
}
