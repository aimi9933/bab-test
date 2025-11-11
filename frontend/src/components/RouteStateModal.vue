<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-backdrop" role="dialog" aria-modal="true" aria-label="Route State">
      <div class="modal-panel">
        <header class="modal-header">
          <div>
            <h2>Route State</h2>
            <p class="modal-subtitle">{{ routeState?.routeName }} (ID: {{ routeState?.routeId }})</p>
          </div>
          <button class="btn btn-secondary" type="button" @click="$emit('close')">
            Close
          </button>
        </header>
        <div class="modal-body">
          <div v-if="routeState" class="state-content">
            <h3>Current State</h3>
            <pre class="state-json">{{ JSON.stringify(routeState.state, null, 2) }}</pre>
          </div>
        </div>
        <footer class="modal-footer">
          <button class="btn btn-secondary" type="button" @click="$emit('close')">
            Close
          </button>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import type { RoutingStateResponse } from '@/types/routes';

interface Props {
  visible: boolean;
  routeState: RoutingStateResponse | null;
}

defineProps<Props>();

defineEmits<{
  (event: 'close'): void;
}>();
</script>

<style scoped>
.state-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.state-content h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
}

.state-json {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 12px;
  font-family: monospace;
  font-size: 0.875rem;
  line-height: 1.4;
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}
</style>