import { describe, expect, it } from 'vitest'

import { projectProgramRanking } from './ranking'

const response = {
  year: 2026,
  program_code: '085404',
  program_name: null,
  disclaimer: '仅供参考。',
  position: { score: 350, provisional_rank: 2, schools_passing: 2, total_schools: 3 },
  rows: [
    {
      school_name: '甲大学',
      rank: 1,
      total_score: 370,
      political: null,
      foreign_language: null,
      subject_one: null,
      subject_two: null,
      unit_count: 2,
      department: '计算机学院',
      province: '北京',
      zone: 'A',
      is_985: true,
      is_211: true,
      is_self_drawn: false,
      source_file: 'x.xlsx',
    },
    {
      school_name: '乙大学',
      rank: 2,
      total_score: 340,
      political: null,
      foreign_language: null,
      subject_one: null,
      subject_two: null,
      unit_count: 1,
      department: null,
      province: '广东',
      zone: 'A',
      is_985: false,
      is_211: false,
      is_self_drawn: false,
      source_file: 'y.xlsx',
    },
  ],
} as unknown as Parameters<typeof projectProgramRanking>[0]

describe('projectProgramRanking', () => {
  it('maps rows and keeps the shared rank semantics', () => {
    const model = projectProgramRanking(response, 350)
    expect(model.rows.map((r) => r.rank)).toEqual([1, 2])
    expect(model.rows[0].school).toBe('甲大学')
  })

  it('marks which schools the score already clears', () => {
    const model = projectProgramRanking(response, 350)
    expect(model.rows.map((r) => r.passing)).toEqual([false, true])
  })

  it('exposes the position when a score is given', () => {
    const model = projectProgramRanking(response, 350)
    expect(model.position?.rank).toBe(2)
    expect(model.position?.totalSchools).toBe(3)
  })
})
