import { createRouter, createWebHistory } from 'vue-router';
import ProvidersView from '@/views/ProvidersView.vue';
import ObservabilityView from '@/views/ObservabilityView.vue';
import RoutesView from '@/views/RoutesView.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'providers',
      component: ProvidersView,
    },
    {
      path: '/routes',
      name: 'routes',
      component: RoutesView,
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
