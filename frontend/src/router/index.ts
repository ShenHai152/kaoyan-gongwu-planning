// View routing. Navigation is projection-only: it selects which presenter
// renders. No route owns data; each view fetches from the backend itself.
import { createRouter, createWebHistory } from 'vue-router'

import { t } from '@/locale'

export const routes = [
  { path: '/', redirect: '/reach-match-safety' },
  {
    path: '/reach-match-safety',
    name: 'reach-match-safety',
    component: () => import('@/views/ReachMatchSafetyView.vue'),
    meta: { title: t.reachMatch.heading, eyebrow: t.reachMatch.eyebrow, lead: t.reachMatch.lead },
  },
  {
    path: '/ranking',
    name: 'ranking',
    component: () => import('@/views/RankingView.vue'),
    meta: { title: t.ranking.heading, eyebrow: t.ranking.eyebrow, lead: t.ranking.lead },
  },
  {
    path: '/heat',
    name: 'heat',
    component: () => import('@/views/HeatRankingView.vue'),
    meta: { title: t.heat.heading, eyebrow: t.heat.eyebrow, lead: t.heat.lead },
  },
  {
    path: '/ai-report',
    name: 'ai-report',
    component: () => import('@/views/AiReportView.vue'),
    meta: { title: t.aiReport.heading, eyebrow: t.aiReport.eyebrow, lead: t.aiReport.lead },
  },
  { path: '/:pathMatch(.*)*', redirect: '/reach-match-safety' },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

export default router
