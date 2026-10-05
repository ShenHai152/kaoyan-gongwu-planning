<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { fetchHeatRanking, type HeatRankingQuery } from '@/api/client'
import StatStrip, { type StatCard } from '@/components/StatStrip.vue'
import { t } from '@/locale'
import { projectHeatRanking, type HeatViewModel } from '@/projection/heatRanking'

const form = reactive({
  sort: 'net' as 'net' | 'comp',
  subjectClass: '',
  tier: '',
})

const loading = ref(false)
const error = ref(false)
const model = ref<HeatViewModel | null>(null)

// Facets come from the loaded page, not a hardcoded list, so they cannot drift
// from the data (e.g. subject_class carries 22408 / 非408 / 混合).
const subjectOptions = ref<string[]>([])
const tierOptions = ref<string[]>([])

async function load() {
  loading.value = true
  error.value = false
  try {
    const query: HeatRankingQuery = { sort: form.sort }
    if (form.subjectClass) query.subject_class = form.subjectClass
    if (form.tier) query.tier = form.tier
    const response = await fetchHeatRanking(query)
    model.value = projectHeatRanking(response)
    if (!subjectOptions.value.length) subjectOptions.value = facets('subjectClass')
    if (!tierOptions.value.length) tierOptions.value = facets('tier')
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
}

function facets(field: 'subjectClass' | 'tier'): string[] {
  const values = new Set<string>()
  for (const row of model.value?.rows ?? []) {
    const value = row[field]
    if (value) values.add(value)
  }
  return [...values].sort()
}

function reset() {
  form.sort = 'net'
  form.subjectClass = ''
  form.tier = ''
  void load()
}

onMounted(() => void load())

const hasResult = computed(() => model.value !== null && !model.value.isEmpty)

const statCards = computed<StatCard[]>(() => {
  const rows = model.value?.rows ?? []
  const top = rows[0]
  const cards: StatCard[] = [
    { key: 'count', label: t.heat.heading, value: rows.length, unit: '条', tone: 'rank' },
  ]
  if (top) {
    cards.push({
      key: 'top',
      label: t.heat.hit,
      value: top.heat ?? '—',
      hint: `${top.school} · ${top.college}`,
      tone: 'reach',
    })
  }
  cards.push({
    key: 'excluded',
    label: t.heat.excludedLabel,
    value: model.value?.excludedMissing ?? 0,
    unit: '条',
    hint: t.heat.coverageHint,
    tone: 'match',
  })
  return cards
})
</script>

<template>
  <section class="rms">
    <header class="page-head">
      <p class="page-head__eyebrow">{{ t.heat.eyebrow }}</p>
      <h1 class="page-head__title">{{ t.heat.heading }}</h1>
      <p class="page-head__lead">{{ t.heat.lead }}</p>
    </header>

    <el-alert type="info" :closable="false" class="state" :title="t.heat.coverageNote" />

    <section class="panel panel--form">
      <div class="panel__head">
        <h2 class="panel__title">{{ t.heat.heading }}</h2>
        <p class="panel__hint">
          {{
            t.heat.coverage
              .replace('{rows}', String(model?.rows.length ?? 0))
              .replace('{excluded}', String(model?.excludedMissing ?? 0))
          }}
        </p>
      </div>
      <el-form class="rms-form" label-position="top" @submit.prevent="load">
        <div class="grid">
          <el-form-item :label="t.heat.sort">
            <el-select v-model="form.sort" style="width: 100%">
              <el-option :label="t.heat.sortNet" value="net" />
              <el-option :label="t.heat.sortComp" value="comp" />
            </el-select>
          </el-form-item>
          <el-form-item :label="t.heat.subjectClass">
            <el-select v-model="form.subjectClass" clearable :placeholder="t.common.anyOption" style="width: 100%">
              <el-option v-for="value in subjectOptions" :key="value" :label="value" :value="value" />
            </el-select>
          </el-form-item>
          <el-form-item :label="t.common.tier">
            <el-select v-model="form.tier" clearable :placeholder="t.common.anyOption" style="width: 100%">
              <el-option v-for="value in tierOptions" :key="value" :label="value" :value="value" />
            </el-select>
          </el-form-item>
        </div>
        <div class="actions">
          <el-button type="primary" native-type="submit" size="large" :loading="loading">
            {{ t.common.query }}
          </el-button>
          <el-button size="large" @click="reset">{{ t.common.reset }}</el-button>
        </div>
      </el-form>
    </section>

    <el-alert v-if="error" type="error" :closable="false" class="state">
      <template #title>
        {{ t.common.error }}
        <el-button link type="primary" @click="load">{{ t.common.retry }}</el-button>
      </template>
    </el-alert>

    <el-alert
      v-if="model && model.isEmpty"
      type="info"
      :closable="false"
      class="state"
      :title="t.common.empty"
    />

    <div v-if="hasResult && model" class="result">
      <StatStrip :cards="statCards" />

      <section class="panel panel--result">
        <el-table :data="model.rows" row-key="school" class="band-table" :row-class-name="() => 'dense-row'">
          <el-table-column :label="t.ranking.rank" width="80" align="right">
            <template #default="{ row }"><span class="num">{{ row.rank }}</span></template>
          </el-table-column>
          <el-table-column :label="t.common.school" min-width="200">
            <template #default="{ row }">
              <span class="school">{{ row.school }}</span>
              <span class="heat-college">{{ row.college }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="t.heat.hit" width="110" align="right">
            <template #default="{ row }">
              <span class="num heat-value">{{ row.heat ?? '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="t.heat.wdCount" width="110" align="right">
            <template #default="{ row }"><span class="num">{{ row.discussion ?? '—' }}</span></template>
          </el-table-column>
          <el-table-column :label="t.heat.line2026" width="120" align="right">
            <template #default="{ row }"><span class="num">{{ row.line2026 ?? '—' }}</span></template>
          </el-table-column>
          <el-table-column :label="t.heat.admitCount" width="120" align="right">
            <template #default="{ row }"><span class="num">{{ row.admitCount ?? '—' }}</span></template>
          </el-table-column>
          <el-table-column :label="t.common.tier" width="110">
            <template #default="{ row }"><span class="region">{{ row.tier ?? '—' }}</span></template>
          </el-table-column>
          <el-table-column :label="t.common.region" width="110">
            <template #default="{ row }"><span class="region">{{ row.region ?? '—' }}</span></template>
          </el-table-column>
        </el-table>
      </section>

      <p class="disclaimer">
        <strong>{{ t.common.disclaimerLabel }}</strong>{{ model.disclaimer }}
      </p>
    </div>
  </section>
</template>

<style scoped src="./reach-match.css"></style>
<style scoped>
.heat-college {
  display: block;
  color: var(--color-muted-foreground);
  font-size: 12px;
}

.heat-value {
  font-weight: 700;
  color: var(--band-reach);
}
</style>
