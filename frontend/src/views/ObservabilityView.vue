<template>
  <div class="observability-view">
    <ObservabilityDashboard />
  </div>
</template>

<script setup lang="ts">
import ObservabilityDashboard from '@/components/ObservabilityDashboard.vue';
</script>

<style scoped>
.observability-view {
  width: 100%;
  min-height: 100vh;
  background-color: #f5f5f5;
}
</style>
