import { describe, expect, it } from 'vitest'

import { projectHeatRanking } from './heatRanking'

const response = {
  sort: 'net',
  filters: {},
  excluded_missing: 91,
  disclaimer: '仅供参考。',
  rows: [
    {
      rank: 1,
      school_name: '南京大学',
      college: '人工智能学院',
      direction: '',
      subject_class: '待确认',
      province: '江苏',
      region: '华东',
      tier: '985',
      heat_net: 95,
      heat_comp: 56,
      wd_count: 5,
      nn_rate_raw: null,
      line_2026_value: 380,
      admit_cnt_value: 14,
      src_label: '网络热度',
      source_file: '001-南京大学.json',
    },
  ],
} as unknown as Parameters<typeof projectHeatRanking>[0]

describe('projectHeatRanking', () => {
  it('uses the net heat value when sorting by net', () => {
    const model = projectHeatRanking(response)
    expect(model.rows[0].heat).toBe(95)
    expect(model.rows[0].school).toBe('南京大学')
  })

  it('uses the competition heat value when sorting by comp', () => {
    const model = projectHeatRanking({ ...response, sort: 'comp' })
    expect(model.rows[0].heat).toBe(56)
  })

  it('carries the excluded count so the coverage limit is visible', () => {
    expect(projectHeatRanking(response).excludedMissing).toBe(91)
  })
})
