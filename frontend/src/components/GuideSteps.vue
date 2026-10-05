<script setup lang="ts">
// Progressive-disclosure guide: explains a page before the user has a result.
// Same three-step shape as the reach-match page, reused across views.
export interface GuideStep {
  index: string
  title: string
  body: string
}

defineProps<{ title: string; steps: GuideStep[] }>()
</script>

<template>
  <section class="panel panel--guide">
    <div class="panel__head">
      <h2 class="panel__title">{{ title }}</h2>
    </div>
    <ol class="guide">
      <li v-for="step in steps" :key="step.index" class="guide__step">
        <span class="guide__index" aria-hidden="true">{{ step.index }}</span>
        <span class="guide__body">
          <span class="guide__title">{{ step.title }}</span>
          <span class="guide__text">{{ step.body }}</span>
        </span>
      </li>
    </ol>
  </section>
</template>

<style scoped src="../views/reach-match.css"></style>
<style scoped>
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
</style>
