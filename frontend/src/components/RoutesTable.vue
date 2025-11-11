<template>
  <div class="routes-table">
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Mode</th>
          <th>Status</th>
          <th>Providers</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="route in routes" :key="route.id">
          <td>
            <strong>{{ route.name }}</strong>
            <div class="route-meta">
              Created {{ formatDate(route.createdAt) }}
            </div>
          </td>
          <td>
            <span class="mode-badge" :class="`mode-${route.mode}`">
              {{ route.mode }}
            </span>
          </td>
          <td>
            <span class="status-badge" :class="{ active: route.isActive }">
              {{ route.isActive ? 'Active' : 'Inactive' }}
            </span>
          </td>
          <td>
            <div class="provider-list">
              <div v-for="node in route.nodes" :key="node.id" class="provider-item">
                <span class="provider-name">{{ node.apiName }}</span>
                <span class="provider-models">{{ node.models.length }} models</span>
                <span class="provider-strategy">{{ node.strategy }}</span>
              </div>
              <div v-if="route.nodes.length === 0 && route.mode === 'auto'" class="config-info">
                <span v-if="(route.config as any)?.selectedModels?.length > 0" class="provider-models">
                  {{ (route.config as any).selectedModels.length }} models configured
                </span>
                <span v-else class="no-providers">No models configured</span>
              </div>
              <div v-if="route.nodes.length === 0 && route.mode !== 'auto'" class="no-providers">
                No providers configured
              </div>
            </div>
          </td>
          <td>
            <div class="actions">
              <button
                class="btn btn-small btn-secondary"
                @click="$emit('test', route)"
                :disabled="testingId === route.id"
              >
                <span v-if="testingId === route.id">Testing…</span>
                <span v-else>Test</span>
              </button>
              <button
                class="btn btn-small btn-secondary"
                @click="$emit('state', route)"
              >
                State
              </button>
              <button
                class="btn btn-small btn-secondary"
                @click="$emit('edit', route)"
              >
                Edit
              </button>
              <button
                class="btn btn-small btn-danger"
                @click="$emit('delete', route)"
              >
                Delete
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Test Results -->
    <div v-if="Object.keys(testResults).length > 0" class="test-results">
      <h4>Last Test Results</h4>
      <div v-for="(result, routeId) in testResults" :key="routeId" class="test-result">
        <strong>Route {{ routeId }}:</strong>
        Selected {{ result.providerName }} with model {{ result.model }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ModelRoute, RoutingSelectionResponse } from '@/types/routes';

interface Props {
  routes: ModelRoute[];
  testingId?: number | null;
  testResults: Record<number, RoutingSelectionResponse>;
}

defineProps<Props>();

defineEmits<{
  edit: [route: ModelRoute];
  delete: [route: ModelRoute];
  test: [route: ModelRoute];
  state: [route: ModelRoute];
}>();

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString();
};
</script>

<style scoped>
.routes-table {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  background: #f8fafc;
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
}

td {
  padding: 16px;
  border-bottom: 1px solid #f3f4f6;
}

tr:last-child td {
  border-bottom: none;
}

.route-meta {
  font-size: 0.875rem;
  color: #6b7280;
  margin-top: 4px;
}

.mode-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.mode-auto {
  background: #dbeafe;
  color: #1e40af;
}

.mode-specific {
  background: #fef3c7;
  color: #92400e;
}

.mode-multi {
  background: #ede9fe;
  color: #5b21b6;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  background: #fee2e2;
  color: #991b1b;
}

.status-badge.active {
  background: #d1fae5;
  color: #065f46;
}

.provider-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.provider-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
}

.provider-name {
  font-weight: 500;
  color: #374151;
}

.provider-models {
  color: #6b7280;
  font-size: 0.75rem;
}

.provider-strategy {
  padding: 2px 6px;
  background: #f3f4f6;
  border-radius: 3px;
  font-size: 0.7rem;
  color: #4b5563;
}

.no-providers {
  color: #9ca3af;
  font-style: italic;
  font-size: 0.875rem;
}

.actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.test-results {
  margin-top: 16px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 6px;
}

.test-results h4 {
  margin: 0 0 8px 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.test-result {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 4px;
}

.btn-small {
  padding: 4px 8px;
  font-size: 0.75rem;
}

.btn-danger {
  background: #dc2626;
  color: white;
}

.btn-danger:hover {
  background: #b91c1c;
}
</style>