<template>
  <div class="table-wrapper">
    <table>
      <thead>
        <tr>
          <th scope="col">Provider</th>
          <th scope="col">Base URL</th>
          <th scope="col">Models</th>
          <th scope="col">Health</th>
          <th scope="col">Status</th>
          <th scope="col">Latency</th>
          <th scope="col">Last test</th>
          <th scope="col" class="sr-only">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="provider in providers" :key="provider.id">
          <td>
            <div class="provider-cell">
              <div class="provider-name">{{ provider.name }}</div>
              <span class="badge" :class="provider.isActive ? 'success' : 'neutral'">
                {{ provider.isActive ? 'Active' : 'Inactive' }}
              </span>
            </div>
          </td>
          <td>
            <div class="provider-meta">
              <span class="mono">{{ provider.baseUrl }}</span>
            </div>
          </td>
          <td>
            <div class="model-list">
              <span v-for="model in provider.models" :key="model" class="badge neutral">{{ model }}</span>
            </div>
          </td>
          <td>
            <span class="badge" :class="healthBadgeClass(provider.isHealthy)">
              {{ provider.isHealthy ? 'Healthy' : 'Unhealthy' }}
            </span>
            <div v-if="provider.consecutiveFailures > 0" class="test-meta">
              <span>Failures: {{ provider.consecutiveFailures }}</span>
            </div>
          </td>
          <td>
            <span class="badge" :class="statusBadgeClass(provider.status)">
              {{ formatStatus(provider.status) }}
            </span>
            <div v-if="testResults[provider.id]?.detail" class="test-meta">
              <span>Detail: {{ testResults[provider.id]?.detail }}</span>
            </div>
          </td>
          <td>
            <div class="test-meta">
              <span>{{ formatLatency(provider.latencyMs ?? testResults[provider.id]?.latencyMs ?? null) }}</span>
              <span v-if="testResults[provider.id]?.statusCode">
                Status code: {{ testResults[provider.id]?.statusCode }}
              </span>
            </div>
          </td>
          <td>
            <div class="test-meta">
              <span>{{ formatLastTested(provider.lastTestedAt ?? testResults[provider.id]?.completedAt ?? null) }}</span>
            </div>
          </td>
          <td>
            <div class="table-actions">
              <button class="btn btn-secondary" type="button" @click="$emit('edit', provider)">
                Edit
              </button>
              <button
                class="btn btn-secondary"
                type="button"
                :disabled="testingId === provider.id"
                @click="$emit('test', provider)"
              >
                <span v-if="testingId === provider.id">Testing…</span>
                <span v-else>Test</span>
              </button>
              <button
                :class="['btn', provider.isHealthy ? 'btn-warning' : 'btn-success']"
                type="button"
                @click="$emit('health-toggle', provider)"
              >
                {{ provider.isHealthy ? 'Disable' : 'Enable' }}
              </button>
              <button class="btn btn-danger" type="button" @click="$emit('delete', provider)">
                Delete
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import type { Provider, ProviderTestResult } from '@/types/providers';

interface Props {
  providers: Provider[];
  testingId: number | null;
  testResults: Record<number, ProviderTestResult>;
}

defineProps<Props>();

defineEmits<{
  (event: 'edit', provider: Provider): void;
  (event: 'delete', provider: Provider): void;
  (event: 'test', provider: Provider): void;
  (event: 'health-toggle', provider: Provider): void;
}>();

const healthBadgeClass = (isHealthy: boolean) => {
  return isHealthy ? 'success' : 'error';
};

const statusBadgeClass = (status: string) => {
  const normalized = status.toLowerCase();
  if (normalized === 'online') return 'success';
  if (normalized === 'offline' || normalized === 'error') return 'error';
  if (normalized === 'degraded') return 'warning';
  return 'neutral';
};

const formatStatus = (status: string) => {
  if (!status) return 'Unknown';
  return status.charAt(0).toUpperCase() + status.slice(1);
};

const formatLatency = (latency: number | null) => {
  if (!latency && latency !== 0) return '—';
  return `${latency.toFixed(0)} ms`;
};

const formatLastTested = (timestamp: string | null) => {
  if (!timestamp) return 'Never';
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return '—';
  }
  return date.toLocaleString();
};
</script>

<style scoped>
.provider-cell {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.provider-name {
  font-weight: 600;
  font-size: 1rem;
}

.provider-meta {
  color: #475569;
  font-size: 0.85rem;
  line-height: 1.4;
}

.mono {
  font-family: 'JetBrains Mono', 'Fira Code', 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
  word-break: break-all;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}
</style>
