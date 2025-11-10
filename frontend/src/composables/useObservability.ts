import { computed, ref } from 'vue';
import { api, type AppStats, type LogsResponse } from '@/services/api';

export function useObservability() {
  const stats = ref<AppStats | null>(null);
  const logs = ref<LogsResponse>({ logs: [], total: 0 });
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  const fetchStats = async () => {
    try {
      isLoading.value = true;
      error.value = null;
      stats.value = await api.getStats();
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch stats';
    } finally {
      isLoading.value = false;
    }
  };

  const fetchLogs = async (limit: number = 50) => {
    try {
      isLoading.value = true;
      error.value = null;
      logs.value = await api.getLogs(limit);
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch logs';
    } finally {
      isLoading.value = false;
    }
  };

  const uptimeDisplay = computed(() => {
    if (!stats.value) return 'N/A';
    const seconds = Math.floor(stats.value.uptime_seconds);
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  });

  const healthSummary = computed(() => {
    if (!stats.value) {
      return { healthy: 0, degraded: 0, warning: 0 };
    }

    const totalRequests = stats.value.total_requests;
    const errorRate = stats.value.error_rate;

    return {
      healthy: errorRate < 5 ? 1 : 0,
      degraded: errorRate >= 5 && errorRate < 20 ? 1 : 0,
      warning: errorRate >= 20 ? 1 : 0,
      totalRequests,
      errorRate: errorRate.toFixed(2),
    };
  });

  const topEndpoints = computed(() => {
    if (!stats.value || !stats.value.endpoints) return [];
    return Object.entries(stats.value.endpoints)
      .map(([endpoint, data]: [string, any]) => ({
        endpoint,
        count: data.count,
        avgDuration: data.avg_duration_ms.toFixed(2),
        errorCount: data.error_count,
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);
  });

  return {
    stats,
    logs,
    isLoading,
    error,
    fetchStats,
    fetchLogs,
    uptimeDisplay,
    healthSummary,
    topEndpoints,
  };
}
