<script setup lang="ts">
import { RouterLink, RouterView, useRoute } from 'vue-router'

import { t } from '@/locale'

// Navigation is projection-only: the active key comes from the route, and the
// labels come from the locale layer.
const route = useRoute()
const navItems = [
  { key: 'reach-match-safety', to: '/reach-match-safety', label: t.nav.reachMatch },
  { key: 'ranking', to: '/ranking', label: t.nav.rank },
  { key: 'heat', to: '/heat', label: t.nav.heat },
  { key: 'ai-report', to: '/ai-report', label: t.nav.aiReport },
]
</script>

<template>
  <div class="app-shell">
    <header class="app-bar">
      <div class="app-bar__inner">
        <a class="brand" href="/" aria-label="考研择校助手">
          <span class="brand__mark" aria-hidden="true">研</span>
          <span class="brand__text">
            <span class="brand__title">{{ t.app.title }}</span>
            <span class="brand__subtitle">{{ t.app.subtitle }}</span>
          </span>
        </a>
        <nav class="app-nav" :aria-label="t.nav.label">
          <RouterLink
            v-for="item in navItems"
            :key="item.key"
            :to="item.to"
            class="app-nav__item"
            :class="{ 'is-active': route.name === item.key }"
          >
            {{ item.label }}
          </RouterLink>
        </nav>
      </div>
    </header>
    <main class="app-main">
      <RouterView v-slot="{ Component }">
        <component :is="Component" />
      </RouterView>
    </main>
    <footer class="app-foot">
      <span>{{ t.app.title }} · {{ t.app.subtitle }}</span>
    </footer>
  </div>
</template>

<style>
:root {
  /* Design tokens: shared design system (Analytics Dashboard palette). */
  --color-primary: #1e40af;
  --color-primary-strong: #1e3a5f;
  --color-secondary: #3b82f6;
  --color-accent: #d97706;
  --color-background: #f8fafc;
  --color-surface: #f1f5f9;
  --color-card: #ffffff;
  --color-foreground: #0f172a;
  --color-muted: #e9eef6;
  --color-muted-foreground: #475569;
  --color-border: #dbeafe;
  --color-border-strong: #cbd5e1;
  --color-ring: #1e40af;
  --band-reach: #b45309;
  --band-match: #2563eb;
  --band-safety: #15803d;
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.06);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);
  --shadow-lg: 0 14px 30px rgba(15, 23, 42, 0.12);
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --font-display: 'Noto Serif SC', 'Songti SC', 'STSong', Georgia, serif;
  --font-body: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', system-ui, -apple-system,
    'Segoe UI', sans-serif;
  --font-data: ui-monospace, 'SFMono-Regular', 'JetBrains Mono', Menlo, Consolas, monospace;
  --el-color-primary: var(--color-primary);
  /* Element Plus derives these from the base color via SCSS mix; the runtime
     vars do not recompute, so mirror the same mix ratios here. */
  --el-color-primary-light-3: #6279c7;
  --el-color-primary-light-5: #8fa0d7;
  --el-color-primary-light-7: #bcc6e7;
  --el-color-primary-light-8: #d2d9ef;
  --el-color-primary-light-9: #e9ecf7;
  --el-color-primary-dark-2: #18338c;
  --el-border-radius-base: var(--radius-sm);
}

* {
  box-sizing: border-box;
}

html {
  -webkit-text-size-adjust: 100%;
}

body {
  margin: 0;
  background-color: var(--color-background);
  background-image:
    radial-gradient(1100px 520px at 12% -8%, rgba(30, 64, 175, 0.08), transparent 60%),
    radial-gradient(900px 460px at 92% -4%, rgba(217, 119, 6, 0.07), transparent 55%);
  background-repeat: no-repeat;
  color: var(--color-foreground);
  font-family: var(--font-body);
  font-size: 16px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

a {
  color: inherit;
  text-decoration: none;
}

.app-shell {
  display: flex;
  min-height: 100vh;
  flex-direction: column;
}

.app-bar {
  position: sticky;
  top: 0;
  z-index: 20;
  background: linear-gradient(120deg, var(--color-primary-strong) 0%, var(--color-primary) 70%, #24509a 100%);
  color: #ffffff;
  box-shadow: var(--shadow-md);
}

.app-bar__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 12px 24px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.brand__mark {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  flex: none;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.25);
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.brand__text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand__title {
  font-family: var(--font-display);
  font-size: 19px;
  font-weight: 600;
  letter-spacing: 0.02em;
  line-height: 1.25;
}

.brand__subtitle {
  color: rgba(255, 255, 255, 0.72);
  font-size: 12px;
  letter-spacing: 0.08em;
}

.app-nav {
  display: flex;
  align-items: center;
  gap: 4px;
  overflow-x: auto;
  scrollbar-width: none;
}

.app-nav::-webkit-scrollbar {
  display: none;
}

.app-nav__item {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 999px;
  color: rgba(255, 255, 255, 0.78);
  font-size: 14px;
  white-space: nowrap;
  cursor: pointer;
  transition: background-color 200ms ease, color 200ms ease;
}

.app-nav__item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.app-nav__item.is-active {
  background: rgba(255, 255, 255, 0.16);
  color: #ffffff;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.35);
}

.app-main {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 24px 56px;
  flex: 1;
}

.app-foot {
  padding: 20px 24px 32px;
  text-align: center;
  color: var(--color-muted-foreground);
  font-size: 12px;
  letter-spacing: 0.04em;
}

@media (max-width: 720px) {
  .app-bar__inner {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding: 12px 16px;
  }

  .app-main {
    padding: 20px 16px 40px;
  }
}

@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
