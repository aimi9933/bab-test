import { createRouter, createWebHistory } from 'vue-router';
import ProvidersView from '@/views/ProvidersView.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'providers',
      component: ProvidersView,
    },
  ],
  scrollBehavior() {
    return { top: 0 };
  },
});

export default router;
