<template>
  <div class="app-shell">
    <header class="app-navbar">
      <div class="app-navbar__brand">
        <span class="app-navbar__dot" aria-hidden="true"></span>
        <span>Provider Control Center</span>
      </div>
      <nav class="app-navbar__actions" aria-label="Primary navigation">
        <RouterLink class="app-navbar__link" to="/">Providers</RouterLink>
        <RouterLink class="app-navbar__link" to="/observability">Observability</RouterLink>
      </nav>
    </header>
    <main class="page-shell">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router';
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-navbar {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background: rgba(248, 250, 252, 0.95);
  backdrop-filter: saturate(180%) blur(10px);
  border-bottom: 1px solid rgba(226, 232, 240, 0.8);
}

.app-navbar__brand {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  font-weight: 700;
  color: #1d4ed8;
}

.app-navbar__dot {
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 9999px;
  background: linear-gradient(120deg, #2563eb 0%, #7c3aed 100%);
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.18);
}

.app-navbar__actions {
  display: inline-flex;
  gap: 1rem;
  font-weight: 600;
  color: #334155;
}

.app-navbar__link {
  position: relative;
  padding-bottom: 0.25rem;
}

.app-navbar__link.router-link-active::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 3px;
  border-radius: 9999px;
  background: linear-gradient(120deg, #2563eb 0%, #7c3aed 100%);
}

@media (max-width: 640px) {
  .app-navbar {
    flex-direction: column;
    gap: 0.75rem;
    align-items: flex-start;
  }
}
</style>
