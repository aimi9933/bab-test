<template>
  <div class="observability-dashboard">
    <div class="dashboard-header">
      <h2>Observability & Monitoring</h2>
      <button @click="refresh" :disabled="isLoading" class="refresh-btn">
        {{ isLoading ? 'Loading...' : 'Refresh' }}
      </button>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <div class="stats-grid">
      <!-- Uptime Card -->
      <div class="stat-card">
        <h3>Uptime</h3>
        <div class="stat-value">{{ uptimeDisplay }}</div>
        <p class="stat-label">Server uptime</p>
      </div>

      <!-- Total Requests Card -->
      <div class="stat-card">
        <h3>Total Requests</h3>
        <div class="stat-value">{{ healthSummary.totalRequests }}</div>
        <p class="stat-label">Since startup</p>
      </div>

      <!-- Error Rate Card -->
      <div class="stat-card">
        <h3>Error Rate</h3>
        <div class="stat-value" :class="getErrorRateClass()">
          {{ healthSummary.errorRate }}%
        </div>
        <p class="stat-label">Last period</p>
      </div>

      <!-- Avg Response Time Card -->
      <div class="stat-card">
        <h3>Avg Response Time</h3>
        <div class="stat-value">
          {{ stats?.average_duration_ms?.toFixed(2) || 'N/A' }}ms
        </div>
        <p class="stat-label">Average duration</p>
      </div>
    </div>

    <!-- Health Summary -->
    <div class="health-summary">
      <h3>Health Status</h3>
      <div class="health-badges">
        <span v-if="healthSummary.healthy > 0" class="badge badge-healthy">✓ Healthy</span>
        <span v-if="healthSummary.degraded > 0" class="badge badge-degraded">⚠ Degraded</span>
        <span v-if="healthSummary.warning > 0" class="badge badge-warning">✗ Warning</span>
        <span v-if="healthSummary.healthy === 0 && healthSummary.degraded === 0 && healthSummary.warning === 0" class="badge badge-info">
          ? Unknown
        </span>
      </div>
    </div>

    <!-- Top Endpoints -->
    <div class="endpoints-section" v-if="topEndpoints.length > 0">
      <h3>Top Endpoints</h3>
      <table class="endpoints-table">
        <thead>
          <tr>
            <th>Endpoint</th>
            <th>Requests</th>
            <th>Avg Time (ms)</th>
            <th>Errors</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="endpoint in topEndpoints" :key="endpoint.endpoint">
            <td class="endpoint-name">{{ endpoint.endpoint }}</td>
            <td>{{ endpoint.count }}</td>
            <td>{{ endpoint.avgDuration }}</td>
            <td :class="endpoint.errorCount > 0 ? 'has-errors' : ''">
              {{ endpoint.errorCount }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Recent Logs -->
    <div class="logs-section">
      <div class="logs-header">
        <h3>Recent Logs</h3>
        <button @click="loadMoreLogs" :disabled="isLoading" class="load-logs-btn">
          Load Logs
        </button>
      </div>
      <div class="logs-container">
        <div v-if="logs.logs.length === 0" class="no-logs">No logs available</div>
        <div v-for="(log, index) in logs.logs" :key="index" class="log-entry" :class="getLevelClass(log.level)">
          <div class="log-header">
            <span class="log-level">{{ log.level }}</span>
            <span class="log-timestamp">{{ formatTimestamp(log.timestamp) }}</span>
            <span v-if="log.request_id" class="log-request-id">{{ log.request_id.substring(0, 8) }}</span>
          </div>
          <div class="log-message">{{ log.message }}</div>
          <div v-if="log.method || log.path" class="log-context">
            <span v-if="log.method" class="log-method">{{ log.method }}</span>
            <span v-if="log.path" class="log-path">{{ log.path }}</span>
            <span v-if="log.status_code" class="log-status" :class="`status-${log.status_code}`">
              {{ log.status_code }}
            </span>
            <span v-if="log.duration_ms" class="log-duration">{{ log.duration_ms.toFixed(2) }}ms</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useObservability } from '@/composables/useObservability';

const {
  stats,
  logs,
  isLoading,
  error,
  fetchStats,
  fetchLogs,
  uptimeDisplay,
  healthSummary,
  topEndpoints,
} = useObservability();

const refresh = async () => {
  await Promise.all([fetchStats(), fetchLogs(50)]);
};

const loadMoreLogs = async () => {
  await fetchLogs(100);
};

const getErrorRateClass = (): string => {
  const rate = parseFloat(healthSummary.value.errorRate);
  if (rate < 5) return 'healthy';
  if (rate < 20) return 'degraded';
  return 'critical';
};

const getLevelClass = (level: string): string => {
  return `level-${level.toLowerCase()}`;
};

const formatTimestamp = (timestamp: string): string => {
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  } catch {
    return timestamp;
  }
};

onMounted(() => {
  refresh();
  // Auto-refresh every 30 seconds
  setInterval(refresh, 30000);
});
</script>

<style scoped>
.observability-dashboard {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 16px;
}

.dashboard-header h2 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.refresh-btn {
  padding: 8px 16px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.refresh-btn:hover:not(:disabled) {
  background-color: #0056b3;
}

.refresh-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 16px;
  border: 1px solid #f5c6cb;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.stat-card h3 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #333;
  margin-bottom: 8px;
}

.stat-value.healthy {
  color: #28a745;
}

.stat-value.degraded {
  color: #ffc107;
}

.stat-value.critical {
  color: #dc3545;
}

.stat-label {
  margin: 0;
  font-size: 12px;
  color: #999;
}

.health-summary {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 24px;
}

.health-summary h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
}

.health-badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.badge {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.badge-healthy {
  background-color: #d4edda;
  color: #155724;
}

.badge-degraded {
  background-color: #fff3cd;
  color: #856404;
}

.badge-warning {
  background-color: #f8d7da;
  color: #721c24;
}

.badge-info {
  background-color: #d1ecf1;
  color: #0c5460;
}

.endpoints-section,
.logs-section {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 24px;
}

.endpoints-section h3,
.logs-header h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.load-logs-btn {
  padding: 6px 12px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background-color 0.3s;
}

.load-logs-btn:hover:not(:disabled) {
  background-color: #0056b3;
}

.load-logs-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.endpoints-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.endpoints-table thead {
  background-color: #f8f9fa;
}

.endpoints-table th {
  padding: 10px;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid #e0e0e0;
  color: #666;
}

.endpoints-table td {
  padding: 10px;
  border-bottom: 1px solid #e0e0e0;
}

.endpoint-name {
  font-family: monospace;
  font-size: 12px;
  color: #0066cc;
}

.endpoints-table .has-errors {
  color: #dc3545;
  font-weight: 500;
}

.logs-container {
  max-height: 500px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background-color: #f8f9fa;
}

.no-logs {
  padding: 20px;
  text-align: center;
  color: #999;
}

.log-entry {
  padding: 12px;
  border-bottom: 1px solid #e0e0e0;
  border-left: 4px solid #ccc;
  background-color: #fff;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.4;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-entry.level-debug {
  border-left-color: #6c757d;
  background-color: #f8f9fa;
}

.log-entry.level-info {
  border-left-color: #0066cc;
  background-color: #f0f4ff;
}

.log-entry.level-warning {
  border-left-color: #ffc107;
  background-color: #fffbf0;
}

.log-entry.level-error {
  border-left-color: #dc3545;
  background-color: #fff0f0;
}

.log-header {
  display: flex;
  gap: 12px;
  margin-bottom: 6px;
  align-items: center;
}

.log-level {
  display: inline-block;
  font-weight: bold;
  min-width: 60px;
}

.log-entry.level-debug .log-level {
  color: #6c757d;
}

.log-entry.level-info .log-level {
  color: #0066cc;
}

.log-entry.level-warning .log-level {
  color: #ffc107;
}

.log-entry.level-error .log-level {
  color: #dc3545;
}

.log-timestamp {
  color: #666;
  font-size: 11px;
}

.log-request-id {
  background-color: #e0e0e0;
  padding: 2px 6px;
  border-radius: 3px;
  color: #333;
  font-size: 11px;
}

.log-message {
  color: #333;
  margin-bottom: 4px;
}

.log-context {
  display: flex;
  gap: 8px;
  color: #666;
  font-size: 11px;
}

.log-method {
  background-color: #e3f2fd;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
}

.log-path {
  color: #0066cc;
}

.log-status {
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
}

.log-status.status-2,
.log-status.status-200,
.log-status.status-201,
.log-status.status-204 {
  background-color: #d4edda;
  color: #155724;
}

.log-status.status-3,
.log-status.status-300,
.log-status.status-301,
.log-status.status-302 {
  background-color: #d1ecf1;
  color: #0c5460;
}

.log-status.status-4,
.log-status.status-400,
.log-status.status-404,
.log-status.status-422 {
  background-color: #fff3cd;
  color: #856404;
}

.log-status.status-5,
.log-status.status-500,
.log-status.status-502,
.log-status.status-503 {
  background-color: #f8d7da;
  color: #721c24;
}

.log-duration {
  color: #666;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .logs-container {
    max-height: 300px;
  }
}
</style>
