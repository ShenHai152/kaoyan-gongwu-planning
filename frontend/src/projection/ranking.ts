// Pure projection: ranking API response -> view model. No side effects.
import type { ProgramRankingResponse } from '@/api/client'

export interface RankingRowView {
  school: string
  rank: number
  totalScore: number
  unitCount: number
  department: string | null
  region: string | null
  zone: string | null
  is985: boolean
  is211: boolean
  isSelfDrawn: boolean
  passing: boolean
}

export interface ScorePositionView {
  score: number
  rank: number | null
  schoolsPassing: number
  totalSchools: number
}

export interface RankingViewModel {
  year: number
  programCode: string | null
  programName: string | null
  rows: RankingRowView[]
  position: ScorePositionView | null
  disclaimer: string
  isEmpty: boolean
}

export function projectProgramRanking(
  response: ProgramRankingResponse,
  score?: number | null,
): RankingViewModel {
  const effectiveScore = score ?? response.position?.score ?? null
  const rows: RankingRowView[] = (response.rows ?? []).map((row) => ({
    school: row.school_name,
    rank: row.rank,
    totalScore: row.total_score,
    unitCount: row.unit_count,
    department: row.department ?? null,
    region: row.province ?? null,
    zone: row.zone ?? null,
    is985: row.is_985,
    is211: row.is_211,
    isSelfDrawn: row.is_self_drawn,
    // Mark the schools the score already clears so the table reads as a ladder.
    passing: effectiveScore !== null && effectiveScore >= row.total_score,
  }))
  const position = response.position
    ? {
        score: response.position.score,
        rank: response.position.provisional_rank ?? null,
        schoolsPassing: response.position.schools_passing,
        totalSchools: response.position.total_schools,
      }
    : null
  return {
    year: response.year,
    programCode: response.program_code ?? null,
    programName: response.program_name ?? null,
    rows,
    position,
    disclaimer: response.disclaimer,
    isEmpty: rows.length === 0,
  }
}
