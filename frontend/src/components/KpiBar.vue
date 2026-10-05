<script setup lang="ts">
// Reach-match KPI strip: three band counts plus the score's rank when known.
// Thin adapter over StatStrip so every page shares one presenter.
import { t } from '@/locale'
import type { ReachMatchViewModel } from '@/projection/reachMatchSafety'
import StatStrip, { type StatCard } from '@/components/StatStrip.vue'

const props = defineProps<{
  model: ReachMatchViewModel
  provisionalRank: number | null
  totalSchools: number | null
}>()

function cards(): StatCard[] {
  const cards: StatCard[] = [
    { key: 'reach', label: t.bands.reach, value: props.model.counts.reach, unit: t.kpi.schools, hint: t.kpi.reachHint, tone: 'reach' },
    { key: 'match', label: t.bands.match, value: props.model.counts.match, unit: t.kpi.schools, hint: t.kpi.matchHint, tone: 'match' },
    { key: 'safety', label: t.bands.safety, value: props.model.counts.safety, unit: t.kpi.schools, hint: t.kpi.safetyHint, tone: 'safety' },
  ]
  if (props.provisionalRank !== null) {
    cards.push({
      key: 'rank',
      label: t.kpi.rank,
      value: `#${props.provisionalRank}`,
      unit: `/ ${props.totalSchools ?? '—'}`,
      hint: t.kpi.rankHint,
      tone: 'rank',
    })
  }
  return cards
}
</script>

<template>
  <StatStrip :cards="cards()" />
</template>
