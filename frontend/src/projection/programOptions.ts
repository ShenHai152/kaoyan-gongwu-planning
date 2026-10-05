// Pure helpers for the selector layer: label formatting and option shaping.
import type { ProgramSearchResponse } from '@/api/client'

export interface ProgramOption {
  code: string
  label: string
  schoolCount: number
}

export function formatProgramLabel(code: string, name: string): string {
  return `${code} ${name}`
}

export function projectProgramOptions(response: ProgramSearchResponse): ProgramOption[] {
  return (response.rows ?? []).map((row) => ({
    code: row.program_code,
    label: formatProgramLabel(row.program_code, row.program_name),
    schoolCount: row.school_count,
  }))
}

export function projectProvinceOptions(
  rows: { name: string; school_count: number }[],
): { value: string; label: string }[] {
  return (rows ?? []).map((row) => ({
    value: row.name,
    label: `${row.name}（${row.school_count}）`,
  }))
}
