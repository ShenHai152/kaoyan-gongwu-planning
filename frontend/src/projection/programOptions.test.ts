import { describe, expect, it } from 'vitest'

import { formatProgramLabel, projectProgramOptions, projectProvinceOptions } from './programOptions'

describe('programOptions', () => {
  it('formats a program label as code + name', () => {
    expect(formatProgramLabel('085404', '计算机技术')).toBe('085404 计算机技术')
  })

  it('projects search rows with the code as the value', () => {
    const options = projectProgramOptions({
      query: '0854',
      truncated: true,
      rows: [{ program_code: '085404', program_name: '计算机技术', school_count: 120 }],
    } as unknown as Parameters<typeof projectProgramOptions>[0])
    expect(options).toEqual([
      { code: '085404', label: '085404 计算机技术', schoolCount: 120 },
    ])
  })

  it('projects province rows with counts in the label', () => {
    expect(projectProvinceOptions([{ name: '北京', school_count: 178 }])).toEqual([
      { value: '北京', label: '北京（178）' },
    ])
  })
})
