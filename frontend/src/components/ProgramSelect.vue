<script setup lang="ts">
// Remote program search: virtual-scrolling dropdown (el-select-v2), debounced
// query, code+name labels, truncation hint. Selected value is the stable code.
import { onMounted, ref } from 'vue'

import { searchPrograms, type ProgramSearchResponse } from '@/api/client'
import { t } from '@/locale'
import { projectProgramOptions, type ProgramOption } from '@/projection/programOptions'

const model = defineModel<string>('code', { default: '' })
const options = ref<ProgramOption[]>([])
const loading = ref(false)
const truncated = ref(false)
const searched = ref(false)
// The truncation hint is only meaningful for a user-entered query; the initial
// empty-query preload must not claim "too many candidates".
const hasQuery = ref(false)

let timer: ReturnType<typeof setTimeout> | undefined

async function run(query: string) {
  loading.value = true
  try {
    const response: ProgramSearchResponse = await searchPrograms(query, 50)
    options.value = projectProgramOptions(response)
    truncated.value = response.truncated
    hasQuery.value = query.trim() !== ''
    searched.value = true
  } finally {
    loading.value = false
  }
}

function onSearch(query: string) {
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => void run(query), 250)
}

// el-select-v2 uses { value, label }; keep the code as the value.
const items = () => options.value.map((o) => ({ value: o.code, label: o.label }))

onMounted(() => void run(''))
</script>

<template>
  <div class="program-select">
    <el-select-v2
      v-model="model"
      filterable
      remote
      clearable
      :remote-method="onSearch"
      :loading="loading"
      :options="items()"
      :placeholder="t.selectors.programPlaceholder"
      style="width: 100%"
    >
      <template #empty>
        <div v-if="searched && !loading" class="hint">
          {{ t.selectors.noProgram }}
        </div>
      </template>
    </el-select-v2>
    <p v-if="truncated && hasQuery" class="truncated">{{ t.selectors.truncated }}</p>
  </div>
</template>

<style scoped>
.truncated {
  color: var(--band-reach);
  font-size: 12px;
  margin: 4px 0 0;
}
.hint {
  color: var(--color-muted-foreground);
  font-size: 12px;
  padding: 8px;
}
</style>
