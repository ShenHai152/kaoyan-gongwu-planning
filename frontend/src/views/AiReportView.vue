<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, reactive, ref } from 'vue'

import { ApiError, requestAiReport, type AiReportResponse } from '@/api/client'
import GuideSteps from '@/components/GuideSteps.vue'
import ProgramSelect from '@/components/ProgramSelect.vue'
import { t } from '@/locale'

const form = reactive({
  score: undefined as number | undefined,
  programCode: '',
  window: 3,
  style: 'neutral' as 'neutral' | 'xuefeng',
})

const loading = ref(false)
const error = ref(false)
const report = ref<AiReportResponse | null>(null)
const STYLE_OPTIONS = [
  { value: 'neutral', label: t.aiReport.styleNeutral },
  { value: 'xuefeng', label: t.aiReport.styleXuefeng },
]

async function submit() {
  if (form.score === undefined || form.score === null) {
    ElMessage.warning(t.aiReport.needScore)
    return
  }
  if (!form.programCode) {
    ElMessage.warning(t.aiReport.needProgram)
    return
  }
  loading.value = true
  error.value = false
  try {
    report.value = await requestAiReport({
      score: form.score,
      program_code: form.programCode,
      window: form.window,
      style: form.style,
    })
  } catch (cause) {
    error.value = true
    if (!(cause instanceof ApiError)) ElMessage.error(t.common.error)
  } finally {
    loading.value = false
  }
}

function reset() {
  form.score = undefined
  form.programCode = ''
  form.window = 3
  form.style = 'neutral'
  report.value = null
  error.value = false
}

const generatedLabel = computed(() =>
  report.value?.generated_by === 'template'
    ? t.aiReport.generatedByTemplate
    : // The backend reports `llm:<model>`; surface the model so the user knows
      // which one answered, without exposing any credential.
      `${t.aiReport.generatedByProvider} · ${report.value?.generated_by.replace('llm:', '')}`,
)
const styleLabel = computed(() =>
  report.value?.style === 'xuefeng' ? t.aiReport.styleXuefeng : t.aiReport.styleNeutral,
)
const guideSteps = [
  { index: '01', title: t.aiReport.guideStep1Title, body: t.aiReport.guideStep1Body },
  { index: '02', title: t.aiReport.guideStep2Title, body: t.aiReport.guideStep2Body },
  { index: '03', title: t.aiReport.guideStep3Title, body: t.aiReport.guideStep3Body },
]
</script>

<template>
  <section class="rms">
    <header class="page-head">
      <p class="page-head__eyebrow">{{ t.aiReport.eyebrow }}</p>
      <h1 class="page-head__title">{{ t.aiReport.heading }}</h1>
      <p class="page-head__lead">{{ t.aiReport.lead }}</p>
    </header>

    <section class="panel panel--form">
      <div class="panel__head">
        <h2 class="panel__title">{{ t.aiReport.heading }}</h2>
        <p class="panel__hint">{{ t.aiReport.formHint }}</p>
      </div>
      <el-form class="rms-form" label-position="top" @submit.prevent="submit">
        <div class="grid">
          <el-form-item :label="t.reachMatch.score" required>
            <el-input-number v-model="form.score" :min="0" :max="500" controls-position="right" />
          </el-form-item>
          <el-form-item :label="t.selectors.program" required>
            <ProgramSelect v-model:code="form.programCode" />
          </el-form-item>
          <el-form-item :label="t.reachMatch.window">
            <el-input-number v-model="form.window" :min="1" :max="10" controls-position="right" />
          </el-form-item>
        </div>
        <div class="advanced__field">
          <span class="advanced__label">{{ t.aiReport.style }}</span>
          <el-radio-group v-model="form.style">
            <el-radio v-for="option in STYLE_OPTIONS" :key="option.value" :value="option.value">
              {{ option.label }}
            </el-radio>
          </el-radio-group>
          <p v-if="form.style === 'xuefeng'" class="help">{{ t.aiReport.styleNoteXuefeng }}</p>
          <p class="help">{{ t.aiReport.generatedByHint }}</p>
        </div>
        <div class="actions">
          <el-button type="primary" native-type="submit" size="large" :loading="loading">
            {{ report ? t.aiReport.regenerate : t.aiReport.generate }}
          </el-button>
          <el-button size="large" @click="reset">{{ t.common.reset }}</el-button>
        </div>
      </el-form>
    </section>

    <el-alert v-if="error" type="error" :closable="false" class="state">
      <template #title>
        {{ t.common.error }}
        <el-button link type="primary" @click="submit">{{ t.common.retry }}</el-button>
      </template>
    </el-alert>

    <GuideSteps v-if="!report" :title="t.aiReport.guideTitle" :steps="guideSteps" />

    <div v-if="report" class="result">
      <section class="panel panel--report">
        <div class="report-head">
          <h2 class="report-summary">{{ report.summary }}</h2>
          <div class="context__chips">
            <span class="chip chip--strong">{{ styleLabel }}</span>
            <span class="chip">{{ generatedLabel }}</span>
            <span class="chip">{{ report.data_refs.length }} {{ t.aiReport.dataRefs }}</span>
            <span class="chip">{{ t.aiReport.session }} #{{ report.session_id }}</span>
          </div>
        </div>

        <article v-for="section in report.sections" :key="section.title" class="report-section">
          <h3 class="report-section__title">{{ section.title }}</h3>
          <ul class="report-points">
            <li v-for="(point, index) in section.points" :key="index">{{ point }}</li>
          </ul>
        </article>

        <div class="report-section">
          <h3 class="report-section__title">{{ t.aiReport.sectionData }}</h3>
          <el-table :data="report.data_refs" class="band-table" :row-class-name="() => 'dense-row'">
            <el-table-column prop="school" :label="t.common.school" min-width="180" />
            <el-table-column :label="t.bands.reach" width="100">
              <template #default="{ row }">{{ t.bands[row.band as 'reach' | 'match' | 'safety'] }}</template>
            </el-table-column>
            <el-table-column :label="t.ranking.line" width="110" align="right">
              <template #default="{ row }"><span class="num">{{ row.reference_line }}</span></template>
            </el-table-column>
            <el-table-column :label="t.reachMatch.columnMargin" width="110" align="right">
              <template #default="{ row }"><span class="num">{{ row.margin }}</span></template>
            </el-table-column>
          </el-table>
        </div>

        <p class="disclaimer">
          <strong>{{ t.common.disclaimerLabel }}</strong>{{ report.disclaimer }}
        </p>
      </section>
    </div>
  </section>
</template>

<style scoped src="./reach-match.css"></style>
<style scoped>
.advanced__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.advanced__label {
  color: var(--color-muted-foreground);
  font-size: 13px;
  font-weight: 500;
}

.help {
  margin: 0;
  color: var(--color-muted-foreground);
  font-size: 12px;
  line-height: 1.7;
}

.panel--report {
  padding: 22px 24px 24px;
}

.report-head {
  padding-bottom: 16px;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--color-muted);
}

.report-summary {
  margin: 0 0 12px;
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  line-height: 1.5;
}

.report-section {
  padding: 14px 0;
  border-bottom: 1px solid var(--color-muted);
}

.report-section__title {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 600;
}

.report-points {
  margin: 0;
  padding-left: 20px;
  color: var(--color-muted-foreground);
  font-size: 14px;
  line-height: 1.9;
}

.report-points li {
  margin-bottom: 2px;
}
</style>
