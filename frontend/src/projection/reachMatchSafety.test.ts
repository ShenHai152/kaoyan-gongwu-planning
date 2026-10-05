import { describe, expect, it } from 'vitest'

import { projectReachMatchSafety } from './reachMatchSafety'

const response = {
  year_to: 2026,
  window: 3,
  score: 350,
  program_code: '085404',
  program_name: null,
  disclaimer: '仅按历年复试线分档，不预测录取概率。',
  rows: [
    {
      school_name: '乙大学',
      band: 'match',
      margin: 10,
      reference_line: 340,
      years_observed: 2,
      lines: [
        { year: 2026, total_score: 340, department: '计算机学院' },
        { year: 2025, total_score: 330, department: null },
      ],
      department: '计算机学院',
      province: '北京',
      zone: 'A',
      is_985: true,
      is_211: true,
      is_self_drawn: false,
      source_file: 'x.xlsx',
    },
    {
      school_name: '甲大学',
      band: 'reach',
      margin: -20,
      reference_line: 370,
      years_observed: 3,
      lines: [{ year: 2026, total_score: 370, department: null }],
      department: null,
      province: '广东',
      zone: 'A',
      is_985: false,
      is_211: false,
      is_self_drawn: false,
      source_file: 'y.xlsx',
    },
  ],
} as unknown as Parameters<typeof projectReachMatchSafety>[0]

describe('projectReachMatchSafety', () => {
  it('groups rows into bands and counts totals', () => {
    const model = projectReachMatchSafety(response)
    expect(model.bands.reach.map((r) => r.school)).toEqual(['甲大学'])
    expect(model.bands.match.map((r) => r.school)).toEqual(['乙大学'])
    expect(model.bands.safety).toEqual([])
    expect(model.total).toBe(2)
    expect(model.isEmpty).toBe(false)
    expect(model.counts).toEqual({ reach: 1, match: 1, safety: 0 })
  })

  it('sorts year lines ascending and keeps the disclaimer', () => {
    const model = projectReachMatchSafety(response)
    expect(model.bands.match[0].lines.map((l) => l.year)).toEqual([2025, 2026])
    expect(model.disclaimer).toContain('不预测录取概率')
  })

  it('reports empty when no rows', () => {
    const model = projectReachMatchSafety({ ...response, rows: [] })
    expect(model.isEmpty).toBe(true)
    expect(model.total).toBe(0)
  })

  it('maps unknown band values to match instead of dropping the row', () => {
    const model = projectReachMatchSafety({
      ...response,
      rows: [{ ...response.rows[0], band: 'mystery' }],
    })
    expect(model.total).toBe(1)
    expect(model.bands.match[0].school).toBe('乙大学')
  })
})
