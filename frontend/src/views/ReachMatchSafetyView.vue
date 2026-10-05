<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

import {
  ApiError,
  fetchProgramRanking,
  fetchProvinces,
  fetchReachMatchSafety,
  type ProgramRankingQuery,
  type ReachMatchSafetyQuery,
} from '@/api/client'
import KpiBar from '@/components/KpiBar.vue'
import ProgramSelect from '@/components/ProgramSelect.vue'
import { t } from '@/locale'
import { projectProvinceOptions } from '@/projection/programOptions'
import {
  projectReachMatchSafety,
  type Band,
  type ReachMatchViewModel,
} from '@/projection/reachMatchSafety'

const form = reactive({
  score: undefined as number | undefined,
  programCode: '',
  window: 3,
  provinces: [] as string[],
  zones: [] as string[],
  is985: false,
  is211: false,
  isSelfDrawn: false,
})

const WINDOW_PRESETS = [1, 3, 5, 8]
const ZONE_OPTIONS = [
  { value: 'A', label: t.reachMatch.zoneA },
  { value: 'B', label: t.reachMatch.zoneB },
]
const provinceOptions = ref<{ value: string; label: string }[]>([])
const loading = ref(false)
const error = ref(false)
const model = ref<ReachMatchViewModel | null>(null)
const provisionalRank = ref<number | null>(null)
const activeBand = ref<Band | null>(null)
const showAdvanced = ref(false)
const BAND_ORDER: Band[] = ['reach', 'match', 'safety']

const bandLabels: Record<Band, string> = {
  reach: t.bands.reach,
  match: t.bands.match,
  safety: t.bands.safety,
}

const bandHints: Record<Band, string> = {
  reach: t.reachMatch.bandReachHint,
  match: t.reachMatch.bandMatchHint,
  safety: t.reachMatch.bandSafetyHint,
}

const programLabel = computed(() => form.programCode || t.reachMatch.anyProgram)
const activeRows = computed(() =>
  activeBand.value && model.value ? model.value.bands[activeBand.value] : [],
)

onMounted(async () => {
  try {
    provinceOptions.value = projectProvinceOptions(await fetchProvinces())
  } catch {
    provinceOptions.value = []
  }
})

function buildQuery(score: number): ReachMatchSafetyQuery {
  const query: ReachMatchSafetyQuery = {
    score,
    window: form.window,
  }
  if (form.programCode) query.program_code = form.programCode
  if (form.provinces.length) query.province = form.provinces
  if (form.zones.length) query.zone = form.zones
  // 985 through 211: 985 ⊆ 211, so matching either yields the 985 set.
  if (form.is985) {
    query.is_985 = true
  } else if (form.is211) {
    query.is_211 = true
  }
  if (form.isSelfDrawn) query.is_self_drawn = true
  return query
}

async function submit() {
  if (form.score === undefined || form.score === null) {
    ElMessage.warning(t.reachMatch.needScore)
    return
  }
  const score = form.score
  if (!form.programCode) {
    ElMessage.warning(t.reachMatch.needProgram)
    return
  }
  loading.value = true
  error.value = false
  try {
    const response = await fetchReachMatchSafety(buildQuery(score))
    model.value = projectReachMatchSafety(response)
    provisionalRank.value = null
    activeBand.value = BAND_ORDER.find((band) => model.value?.bands[band].length) ?? null
    // The rank is a separate ranking projection; fetch it for the same query.
    if (response.year_to !== null && response.year_to !== undefined) {
      const rankingQuery: ProgramRankingQuery = {
        year: response.year_to,
        program_code: form.programCode,
        score,
      }
      try {
        const ranking = await fetchProgramRanking(rankingQuery)
        provisionalRank.value = ranking.position?.provisional_rank ?? null
      } catch {
        provisionalRank.value = null
      }
    }
  } catch (cause) {
    error.value = true
    if (!(cause instanceof ApiError)) ElMessage.error(t.reachMatch.error)
  } finally {
    loading.value = false
  }
}

function reset() {
  form.score = undefined
  form.programCode = ''
  form.window = 3
  form.provinces = []
  form.zones = []
  form.is985 = false
  form.is211 = false
  form.isSelfDrawn = false
  model.value = null
  error.value = false
  provisionalRank.value = null
  activeBand.value = null
  showAdvanced.value = false
}

const hasResult = computed(() => model.value !== null && !model.value.isEmpty)
const hasAdvanced = computed(
  () => form.zones.length > 0 || form.is985 || form.is211 || form.isSelfDrawn,
)
const hasFilters = computed(
  () =>
    form.provinces.length > 0 ||
    form.zones.length > 0 ||
    form.is985 ||
    form.is211 ||
    form.isSelfDrawn,
)
const guideSteps = [
  { index: '01', title: t.reachMatch.guideStep1Title, body: t.reachMatch.guideStep1Body },
  { index: '02', title: t.reachMatch.guideStep2Title, body: t.reachMatch.guideStep2Body },
  { index: '03', title: t.reachMatch.guideStep3Title, body: t.reachMatch.guideStep3Body },
]
</script>

<template>
  <section class="rms">
    <header class="page-head">
      <p class="page-head__eyebrow">{{ t.reachMatch.eyebrow }}</p>
      <h1 class="page-head__title">{{ t.reachMatch.heading }}</h1>
      <p class="page-head__lead">{{ t.reachMatch.lead }}</p>
    </header>

    <section class="panel panel--form">
      <div class="panel__head">
        <h2 class="panel__title">{{ t.reachMatch.formTitle }}</h2>
        <p class="panel__hint">{{ t.reachMatch.formHint }}</p>
      </div>
      <el-form class="rms-form" label-position="top" @submit.prevent="submit">
        <div class="grid">
          <el-form-item :label="t.reachMatch.score" required>
            <el-input-number v-model="form.score" :min="0" :max="500" controls-position="right" />
          </el-form-item>
          <el-form-item :label="t.selectors.program" required>
            <ProgramSelect v-model:code="form.programCode" />
          </el-form-item>
          <el-form-item :label="t.selectors.province">
            <el-select-v2
              v-model="form.provinces"
              multiple
              collapse-tags
              collapse-tags-tooltip
              filterable
              clearable
              :options="provinceOptions"
              :placeholder="t.selectors.provincePlaceholder"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item :label="t.reachMatch.window" class="window-field">
            <div class="window-row">
              <el-input-number v-model="form.window" :min="1" :max="10" controls-position="right" />
              <div class="window-presets">
                <button
                  v-for="preset in WINDOW_PRESETS"
                  :key="preset"
                  type="button"
                  class="window-preset"
                  :class="{ 'is-active': form.window === preset }"
                  @click="form.window = preset"
                >
                  {{ t.reachMatch.windowPreset.replace('{n}', String(preset)) }}
                </button>
              </div>
            </div>
          </el-form-item>
        </div>

        <button
          type="button"
          class="advanced-toggle"
          :aria-expanded="showAdvanced"
          @click="showAdvanced = !showAdvanced"
        >
          <span class="advanced-toggle__caret" :class="{ 'is-open': showAdvanced }" aria-hidden="true">›</span>
          {{ t.reachMatch.advancedTitle }}
          <span v-if="hasAdvanced" class="advanced-toggle__dot" aria-hidden="true" />
        </button>

        <div v-show="showAdvanced" class="advanced">
          <div class="advanced__field">
            <span class="advanced__label">{{ t.reachMatch.filterZone }}</span>
            <el-checkbox-group v-model="form.zones">
              <el-checkbox v-for="zone in ZONE_OPTIONS" :key="zone.value" :value="zone.value">
                {{ zone.label }}
              </el-checkbox>
            </el-checkbox-group>
            <p class="help">{{ t.reachMatch.zoneHelp }}</p>
          </div>
          <div class="advanced__field">
            <span class="advanced__label">{{ t.reachMatch.attrHelp }}</span>
            <div class="switches">
              <el-checkbox v-model="form.is985" :disabled="form.is211">
                {{ t.reachMatch.filter985 }}
              </el-checkbox>
              <el-checkbox v-model="form.is211" :disabled="form.is985">
                {{ t.reachMatch.filter211 }}
              </el-checkbox>
              <el-checkbox v-model="form.isSelfDrawn">{{ t.reachMatch.filterSelfDrawn }}</el-checkbox>
            </div>
          </div>
        </div>

        <div class="actions">
          <el-button type="primary" native-type="submit" size="large" :loading="loading">
            {{ t.reachMatch.submit }}
          </el-button>
          <el-button size="large" @click="reset">{{ t.reachMatch.reset }}</el-button>
          <span class="actions__hint">{{ t.reachMatch.presetHint }}</span>
        </div>
      </el-form>
    </section>

    <el-alert v-if="error" type="error" :closable="false" class="state">
      <template #title>
        {{ t.reachMatch.error }}
        <el-button link type="primary" @click="submit">{{ t.reachMatch.retry }}</el-button>
      </template>
    </el-alert>

    <el-alert
      v-if="model && model.coverageWarning"
      type="warning"
      :closable="false"
      class="state"
      :title="model.coverageWarning"
    />

    <el-alert
      v-if="model && model.isEmpty"
      type="info"
      :closable="false"
      class="state"
      :title="t.reachMatch.empty"
    />

    <section v-if="!hasResult" class="panel panel--guide">
      <div class="panel__head">
        <h2 class="panel__title">{{ t.reachMatch.guideTitle }}</h2>
      </div>
      <ol class="guide">
        <li v-for="step in guideSteps" :key="step.title" class="guide__step">
          <span class="guide__index" aria-hidden="true">{{ step.index }}</span>
          <span class="guide__body">
            <span class="guide__title">{{ step.title }}</span>
            <span class="guide__text">{{ step.body }}</span>
          </span>
        </li>
      </ol>
    </section>

    <div v-if="hasResult && model" class="result">
      <KpiBar :model="model" :provisional-rank="provisionalRank" :total-schools="model.total" />

      <div class="context">
        <div class="context__chips">
          <span class="chip chip--strong">{{ model.score }} 分</span>
          <span class="chip">{{ programLabel }}</span>
          <span class="chip">{{ model.yearTo }} · 近 {{ model.window }} 年</span>
          <span v-if="form.provinces.length" class="chip">
            {{ form.provinces.length > 2 ? `${form.provinces.length} 个省份` : form.provinces.join(' / ') }}
          </span>
          <span v-if="form.zones.length" class="chip">{{ form.zones.join(' / ') }} 区</span>
          <span v-if="form.is985" class="chip">仅 985</span>
          <span v-else-if="form.is211" class="chip">仅 211</span>
          <span v-if="form.isSelfDrawn" class="chip">仅自划线</span>
          <span v-if="!hasFilters" class="chip chip--muted">{{ t.reachMatch.noFilter }}</span>
        </div>
        <p class="context__note">{{ t.reachMatch.resultNote }}</p>
      </div>

      <section class="panel panel--result">
        <div class="bands" role="tablist" :aria-label="t.reachMatch.heading">
          <button
            v-for="band in BAND_ORDER"
            :key="band"
            class="band-tab"
            :class="[`band-tab--${band}`, { 'is-active': activeBand === band }]"
            role="tab"
            type="button"
            :aria-selected="activeBand === band"
            @click="activeBand = band"
          >
            <span class="band-tab__label">{{ bandLabels[band] }}</span>
            <span class="band-tab__count">{{ model.counts[band] }}</span>
          </button>
        </div>

        <p v-if="activeBand" class="band-hint">{{ bandHints[activeBand] }}</p>

        <el-table
          v-if="activeRows.length"
          :data="activeRows"
          row-key="school"
          class="band-table"
          :row-class-name="() => 'dense-row'"
        >
          <el-table-column type="expand">
            <template #default="{ row }">
              <ul class="year-lines">
                <li v-for="line in row.lines" :key="line.year">
                  <span class="year-lines__year">{{ line.year }}</span>
                  <span class="year-lines__score">{{ line.totalScore }}</span>
                  <span v-if="line.department" class="year-lines__dept">{{ line.department }}</span>
                </li>
              </ul>
            </template>
          </el-table-column>
          <el-table-column prop="school" :label="t.reachMatch.columnSchool" min-width="220">
            <template #default="{ row }">
              <span class="school">{{ row.school }}</span>
              <span class="school__tags">
                <span v-if="row.is985" class="tag tag--985">985</span>
                <span v-if="row.is211" class="tag tag--211">211</span>
                <span v-if="row.isSelfDrawn" class="tag tag--self">自划线</span>
              </span>
            </template>
          </el-table-column>
          <el-table-column :label="t.reachMatch.columnReference" width="110" align="right">
            <template #default="{ row }">
              <span class="num">{{ row.referenceLine }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="t.reachMatch.columnMargin" width="110" align="right">
            <template #default="{ row }">
              <span class="num num--margin">{{ row.margin > 0 ? `+${row.margin}` : row.margin }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="t.reachMatch.columnYears" width="110" align="right">
            <template #default="{ row }">
              <span class="num">{{ row.yearsObserved }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="t.reachMatch.columnRegion" width="130">
            <template #default="{ row }">
              <span class="region">{{ row.region ?? '—' }}</span>
              <span v-if="row.zone" class="region__zone">{{ row.zone }}</span>
            </template>
          </el-table-column>
        </el-table>
        <p v-else class="band-empty">{{ t.reachMatch.bandEmpty }}</p>
      </section>

      <p class="disclaimer">
        <strong>{{ t.reachMatch.disclaimerLabel }}</strong>{{ model.disclaimer }}
      </p>
    </div>
  </section>
</template>

<style scoped>
.rms {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-head {
  max-width: 720px;
}

.page-head__eyebrow {
  margin: 0 0 6px;
  color: var(--color-accent);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.18em;
}

.page-head__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 700;
  letter-spacing: 0.01em;
  line-height: 1.25;
}

.page-head__lead {
  margin: 10px 0 0;
  color: var(--color-muted-foreground);
  font-size: 15px;
}

.panel {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-card);
  box-shadow: var(--shadow-sm);
}

.panel--form {
  padding: 20px 22px 22px;
}

.panel__head {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-muted);
}

.panel__title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.panel__hint {
  margin: 0;
  color: var(--color-muted-foreground);
  font-size: 12px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 0 16px;
}

.window-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.window-presets {
  display: flex;
  gap: 4px;
}

.window-preset {
  padding: 5px 9px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-card);
  color: var(--color-muted-foreground);
  font-family: var(--font-body);
  font-size: 12px;
  cursor: pointer;
  transition: background-color 200ms ease, color 200ms ease, border-color 200ms ease;
}

.window-preset:hover {
  border-color: var(--color-secondary);
  color: var(--color-primary);
}

.window-preset.is-active {
  border-color: transparent;
  background: var(--color-primary);
  color: #ffffff;
}

.advanced-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 2px 0 10px;
  padding: 4px 0;
  border: none;
  background: transparent;
  color: var(--color-primary);
  font-family: var(--font-body);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}

.advanced-toggle__caret {
  display: inline-block;
  font-size: 16px;
  line-height: 1;
  transition: transform 200ms ease;
}

.advanced-toggle__caret.is-open {
  transform: rotate(90deg);
}

.advanced-toggle__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-accent);
}

.advanced {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px 24px;
  margin-bottom: 16px;
  padding: 14px 16px;
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.advanced__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
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

.switches {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 20px;
  margin: 2px 0 14px;
}

.actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.actions__hint {
  color: var(--color-muted-foreground);
  font-size: 12px;
}

.actions :deep(.el-button) {
  min-width: 104px;
}

.state {
  margin: 0;
}

.panel--guide {
  padding: 20px 22px 22px;
}

.guide {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.guide__step {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 14px 16px;
  border: 1px solid var(--color-muted);
  border-radius: var(--radius-md);
  background: linear-gradient(170deg, #ffffff 0%, #f7f9ff 100%);
}

.guide__index {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  line-height: 1.1;
  color: var(--color-border-strong);
}

.guide__body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.guide__title {
  font-size: 14px;
  font-weight: 600;
}

.guide__text {
  color: var(--color-muted-foreground);
  font-size: 12px;
  line-height: 1.7;
}

.result {
  display: flex;
  flex-direction: column;
}

.context {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px 16px;
  margin: 4px 0 16px;
}

.context__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: var(--color-card);
  color: var(--color-muted-foreground);
  font-size: 12px;
  line-height: 1.6;
}

.chip--strong {
  border-color: transparent;
  background: var(--color-primary);
  color: #ffffff;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.chip--muted {
  background: var(--color-muted);
  border-style: dashed;
}

.context__note {
  margin: 0;
  color: var(--color-muted-foreground);
  font-size: 12px;
}

.panel--result {
  overflow: hidden;
}

.bands {
  display: flex;
  gap: 4px;
  padding: 10px 14px 0;
  border-bottom: 1px solid var(--color-muted);
}

.band-tab {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--color-muted-foreground);
  font-family: var(--font-body);
  font-size: 14px;
  cursor: pointer;
  transition: color 200ms ease, border-color 200ms ease, background-color 200ms ease;
}

.band-tab:hover {
  background: var(--color-surface);
  color: var(--color-foreground);
}

.band-tab__count {
  padding: 1px 8px;
  border-radius: 999px;
  background: var(--color-muted);
  color: var(--color-muted-foreground);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.band-tab.is-active {
  color: var(--band-tone);
  border-bottom-color: var(--band-tone);
  font-weight: 600;
}

.band-tab.is-active .band-tab__count {
  background: var(--band-tone);
  color: #ffffff;
}

.band-tab--reach {
  --band-tone: var(--band-reach);
}

.band-tab--match {
  --band-tone: var(--band-match);
}

.band-tab--safety {
  --band-tone: var(--band-safety);
}

.band-hint {
  margin: 12px 18px 0;
  color: var(--color-muted-foreground);
  font-size: 12px;
}

.band-table {
  width: 100%;
}

.school {
  font-weight: 600;
}

.school__tags {
  display: inline-flex;
  gap: 4px;
  margin-left: 8px;
  vertical-align: middle;
}

.tag {
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
  line-height: 1.6;
}

.tag--985 {
  background: rgba(30, 64, 175, 0.1);
  color: var(--color-primary);
}

.tag--211 {
  background: rgba(21, 128, 61, 0.1);
  color: var(--band-safety);
}

.tag--self {
  background: rgba(217, 119, 6, 0.12);
  color: var(--band-reach);
}

.num {
  font-family: var(--font-data);
  font-variant-numeric: tabular-nums;
}

.num--margin {
  color: var(--color-muted-foreground);
}

.region {
  color: var(--color-muted-foreground);
}

.region__zone {
  margin-left: 6px;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--color-muted);
  font-size: 11px;
}

.band-empty {
  margin: 0;
  padding: 32px 18px;
  text-align: center;
  color: var(--color-muted-foreground);
  font-size: 13px;
}

.year-lines {
  margin: 0;
  padding: 4px 16px 4px 34px;
  color: var(--color-muted-foreground);
}

.year-lines li {
  display: flex;
  align-items: baseline;
  gap: 14px;
}

.year-lines__year {
  font-family: var(--font-data);
  font-variant-numeric: tabular-nums;
}

.year-lines__score {
  font-family: var(--font-data);
  font-weight: 600;
  color: var(--color-foreground);
  font-variant-numeric: tabular-nums;
}

.year-lines__dept {
  font-size: 12px;
}

.disclaimer {
  margin: 4px 0 0;
  padding: 14px 18px;
  border: 1px solid var(--color-border);
  border-left: 3px solid var(--color-accent);
  border-radius: var(--radius-sm);
  background: var(--color-card);
  color: var(--color-muted-foreground);
  font-size: 12px;
  line-height: 1.7;
}

.disclaimer strong {
  margin-right: 6px;
  color: var(--color-foreground);
}

:deep(.band-table .el-table__header th) {
  background: var(--color-surface);
  color: var(--color-muted-foreground);
  font-weight: 600;
  font-size: 12px;
  letter-spacing: 0.04em;
}

:deep(.band-table .dense-row) {
  height: 40px;
}

:deep(.band-table .el-table__row:hover > td) {
  background: #f5f8ff;
}

:deep(.band-table td),
:deep(.band-table th) {
  border-bottom-color: var(--color-muted);
}

@media (max-width: 720px) {
  .page-head__title {
    font-size: 26px;
  }

  .context {
    align-items: flex-start;
  }
}
</style>
