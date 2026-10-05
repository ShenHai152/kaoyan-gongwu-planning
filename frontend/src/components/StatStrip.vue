<script setup lang="ts">
// Generic KPI strip: a list of { key, label, value, unit, hint, tone } cards.
// One presenter for every data page; the projection decides the numbers.
export interface StatCard {
  key: string
  label: string
  value: string | number
  unit?: string
  hint?: string
  tone?: 'reach' | 'match' | 'safety' | 'rank'
}

defineProps<{ cards: StatCard[] }>()
</script>

<template>
  <div class="stat-strip">
    <div v-for="card in cards" :key="card.key" class="stat" :class="`stat--${card.tone ?? 'rank'}`">
      <span class="stat__rail" aria-hidden="true" />
      <span class="stat__label">{{ card.label }}</span>
      <span class="stat__value">{{ card.value }}</span>
      <span v-if="card.unit" class="stat__unit">{{ card.unit }}</span>
      <span v-if="card.hint" class="stat__hint">{{ card.hint }}</span>
    </div>
  </div>
</template>

<style scoped>
.stat-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 12px;
  margin: 20px 0 12px;
}

.stat {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 16px 18px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-card);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: box-shadow 200ms ease, transform 200ms ease;
}

.stat:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.stat__rail {
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  background: var(--stat-tone, var(--color-primary-strong));
}

.stat__label {
  color: var(--color-muted-foreground);
  font-size: 13px;
  letter-spacing: 0.04em;
}

.stat__value {
  font-family: var(--font-display);
  font-size: 34px;
  font-weight: 700;
  line-height: 1.1;
  color: var(--stat-tone, var(--color-foreground));
  font-variant-numeric: tabular-nums;
}

.stat__unit {
  color: var(--color-muted-foreground);
  font-size: 12px;
}

.stat__hint {
  margin-top: 6px;
  color: var(--color-muted-foreground);
  font-size: 12px;
}

.stat--reach {
  --stat-tone: var(--band-reach);
}

.stat--match {
  --stat-tone: var(--band-match);
}

.stat--safety {
  --stat-tone: var(--band-safety);
}

.stat--rank {
  --stat-tone: var(--color-primary-strong);
  background: linear-gradient(160deg, #ffffff 0%, #f5f8ff 100%);
}
</style>
