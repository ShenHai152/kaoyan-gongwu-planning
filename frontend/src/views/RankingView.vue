<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, reactive, ref } from 'vue'

import { fetchProgramRanking, type ProgramRankingQuery } from '@/api/client'
import ProgramSelect from '@/components/ProgramSelect.vue'
import StatStrip, { type StatCard } from '@/components/StatStrip.vue'
import GuideSteps from '@/components/GuideSteps.vue'
import { t } from '@/locale'
import { projectProgramRanking, type RankingViewModel } from '@/projection/ranking'

const form = reactive({
  year: 2026,
  score: undefined as number | undefined,
  programCode: '',
})

const loading = ref(false)
const error = ref(false)
const model = ref<RankingViewModel | null>(null)
const YEAR_PRESETS = [2026, 2025, 2024]

async function load() {
  if (!form.programCode) {
    ElMessage.warning(t.reachMatch.needProgram)
    return
  }
  loading.value = true
  error.value = false
  try {
    const query: ProgramRankingQuery = {
      year: form.year,
      program_code: form.programCode,
      score: form.score ?? undefined,
    }
    const response = await fetchProgramRanking(query)
    model.value = projectProgramRanking(response, form.score ?? null)
  } catch {
    error.value = true
  } finally {
    loading.value = false
  }
}

function reset() {
  form.year = 2026
  form.score = undefined
  form.programCode = ''
  model.value = null
  error.value = false
}

const hasResult = computed(() => model.value !== null && !model.value.isEmpty)

const guideSteps = [
  { index: '01', title: t.ranking.guideStep1Title, body: t.ranking.guideStep1Body },
  { index: '02', title: t.ranking.guideStep2Title, body: t.ranking.guideStep2Body },
]

const statCards = computed<StatCard[]>(() => {
  const position = model.value?.position
  if (!position) {
    return [
      { key: 'schools', label: t.common.school, value: model.value?.rows.length ?? 0, unit: t.kpi.schools, tone: 'rank' },
    ]
  }
  return [
    { key: 'rank', label: t.ranking.positionTitle, value: position.rank === null ? '—' : `#${position.rank}`, unit: `/ ${position.totalSchools}`, hint: `${position.score} 分`, tone: 'rank' },
    { key: 'passing', label: t.ranking.schoolsPassing, value: position.schoolsPassing, unit: t.kpi.schools, hint: t.ranking.positionLead, tone: 'safety' },
  ]
})
</script>

<template>
  <section class="rms">
    <header class="page-head">
      <p class="page-head__eyebrow">{{ t.ranking.eyebrow }}</p>
      <h1 class="page-head__title">{{ t.ranking.heading }}</h1>
      <p class="page-head__lead">{{ t.ranking.lead }}</p>
    </header>

    <section class="panel panel--form">
      <div class="panel__head">
        <h2 class="panel__title">{{ t.ranking.heading }}</h2>
        <p class="panel__hint">{{ t.ranking.scoreHint }}</p>
      </div>
      <el-form class="rms-form" label-position="top" @submit.prevent="load">
        <div class="grid">
          <el-form-item :label="t.ranking.year" required>
            <div class="window-row">
              <el-input-number v-model="form.year" :min="2017" :max="2026" controls-position="right" />
              <div class="window-presets">
                <button
                  v-for="preset in YEAR_PRESETS"
                  :key="preset"
                  type="button"
                  class="window-preset"
                  :class="{ 'is-active': form.year === preset }"
                  @click="form.year = preset"
                >
                  {{ preset }}
                </button>
              </div>
            </div>
          </el-form-item>
          <el-form-item :label="t.selectors.program" required>
            <ProgramSelect v-model:code="form.programCode" />
          </el-form-item>
          <el-form-item :label="t.common.score">
            <el-input-number v-model="form.score" :min="0" :max="500" controls-position="right" />
          </el-form-item>
        </div>
        <div class="actions">
          <el-button type="primary" native-type="submit" size="large" :loading="loading">
            {{ t.common.query }}
          </el-button>
          <el-button size="large" @click="reset">{{ t.common.reset }}</el-button>
          <span class="actions__hint">{{ t.ranking.yearHint }}</span>
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

    <GuideSteps v-if="!hasResult" :title="t.ranking.guideTitle" :steps="guideSteps" />

    <div v-if="hasResult && model" class="result">
      <StatStrip :cards="statCards" />

      <div class="context">
        <div class="context__chips">
          <span class="chip chip--strong">{{ model.year }} 年</span>
          <span v-if="form.programCode" class="chip">{{ form.programCode }}</span>
          <span v-if="form.score !== undefined" class="chip">{{ form.score }} 分</span>
          <span v-else class="chip chip--muted">{{ t.ranking.noScore }}</span>
        </div>
        <p class="context__note">{{ model.rows.length }} 所院校参与排名</p>
      </div>

      <section class="panel panel--result">
        <el-table :data="model.rows" row-key="school" class="band-table" :row-class-name="() => 'dense-row'">
          <el-table-column :label="t.ranking.rank" width="90" align="right">
            <template #default="{ row }"><span class="num">{{ row.rank }}</span></template>
          </el-table-column>
          <el-table-column prop="school" :label="t.common.school" min-width="220">
            <template #default="{ row }">
              <span class="school">{{ row.school }}</span>
              <span class="school__tags">
                <span v-if="row.is985" class="tag tag--985">985</span>
                <span v-if="row.is211" class="tag tag--211">211</span>
                <span v-if="row.isSelfDrawn" class="tag tag--self">自划线</span>
                <span v-if="row.passing" class="tag tag--pass">{{ t.ranking.reachable }}</span>
              </span>
            </template>
          </el-table-column>
          <el-table-column :label="t.ranking.line" width="120" align="right">
            <template #default="{ row }"><span class="num">{{ row.totalScore }}</span></template>
          </el-table-column>
          <el-table-column :label="t.ranking.unitCount" width="110" align="right">
            <template #default="{ row }"><span class="num">{{ row.unitCount }}</span></template>
          </el-table-column>
          <el-table-column :label="t.reachMatch.columnDepartment" min-width="180">
            <template #default="{ row }">{{ row.department ?? '—' }}</template>
          </el-table-column>
          <el-table-column :label="t.common.region" width="130">
            <template #default="{ row }">
              <span class="region">{{ row.region ?? '—' }}</span>
              <span v-if="row.zone" class="region__zone">{{ row.zone }}</span>
            </template>
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
