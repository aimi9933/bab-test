import { createRouter, createWebHistory } from 'vue-router';
import ProvidersView from '@/views/ProvidersView.vue';
import ObservabilityView from '@/views/ObservabilityView.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'providers',
      component: ProvidersView,
    },
    {
      path: '/observability',
      name: 'observability',
      component: ObservabilityView,
    },
  ],
  scrollBehavior() {
    return { top: 0 };
  },
});

export default router;
