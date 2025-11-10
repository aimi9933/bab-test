import axios, { AxiosError } from 'axios';
import type {
  Provider,
  ProviderCreatePayload,
  ProviderResponse,
  ProviderTestResult,
  ProviderUpdatePayload,
} from '@/types/providers';

interface ProviderTestResponsePayload {
  status: string;
  status_code: number | null;
  latency_ms: number | null;
  detail: string | null;
}

export interface AppStats {
  uptime_seconds: number;
  total_requests: number;
  total_errors: number;
  error_rate: number;
  average_duration_ms: number;
  status_codes: Record<string, number>;
  endpoints: Record<string, any>;
  recent_requests: Array<{
    timestamp: number;
    method: string;
    path: string;
    status_code: number;
    duration_ms: number;
  }>;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  logger: string;
  message: string;
  request_id?: string;
  method?: string;
  path?: string;
  status_code?: number;
  duration_ms?: number;
  [key: string]: any;
}

export interface LogsResponse {
  logs: LogEntry[];
  total: number;
}

export interface ApiError {
  message: string;
  statusCode?: number;
  validationErrors?: Record<string, string[]>;
}

const sanitizedBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

const apiClient = axios.create({
  baseURL: sanitizedBaseUrl || undefined,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const mapProvider = (payload: ProviderResponse): Provider => ({
  id: payload.id,
  name: payload.name,
  baseUrl: payload.base_url,
  models: payload.models,
  isActive: payload.is_active,
  status: payload.status,
  latencyMs: payload.latency_ms,
  lastTestedAt: payload.last_tested_at,
  consecutiveFailures: payload.consecutive_failures,
  isHealthy: payload.is_healthy,
  createdAt: payload.created_at,
  updatedAt: payload.updated_at,
  apiKeyMasked: payload.api_key_masked,
});

const mapTestResult = (payload: ProviderTestResponsePayload): ProviderTestResult => ({
  status: payload.status,
  statusCode: payload.status_code,
  latencyMs: payload.latency_ms,
  detail: payload.detail,
  completedAt: new Date().toISOString(),
});

export const api = {
  async listProviders(): Promise<Provider[]> {
    const { data } = await apiClient.get<ProviderResponse[]>('/api/providers');
    return data.map(mapProvider);
  },
  async createProvider(payload: ProviderCreatePayload): Promise<Provider> {
    const { data } = await apiClient.post<ProviderResponse>('/api/providers', payload);
    return mapProvider(data);
  },
  async updateProvider(id: number, payload: ProviderUpdatePayload): Promise<Provider> {
    const { data } = await apiClient.patch<ProviderResponse>(`/api/providers/${id}`, payload);
    return mapProvider(data);
  },
  async deleteProvider(id: number): Promise<void> {
    await apiClient.delete(`/api/providers/${id}`);
  },
  async testProvider(id: number, timeoutSeconds?: number): Promise<ProviderTestResult> {
    const { data } = await apiClient.post<ProviderTestResponsePayload>(
      `/api/providers/${id}/test`,
      null,
      {
        params: timeoutSeconds ? { timeout: timeoutSeconds } : undefined,
      },
    );
    return mapTestResult(data);
  },
  async setProviderHealth(id: number, isHealthy: boolean): Promise<Provider> {
    const { data } = await apiClient.patch<ProviderResponse>(`/api/providers/${id}/health`, {
      is_healthy: isHealthy,
    });
    return mapProvider(data);
  },
  async getStats(): Promise<AppStats> {
    const { data } = await apiClient.get<AppStats>('/api/admin/stats');
    return data;
  },
  async getLogs(limit: number = 100): Promise<LogsResponse> {
    const { data } = await apiClient.get<LogsResponse>('/api/admin/logs', {
      params: { limit },
    });
    return data;
  },
};

export function toApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<any>;
    const statusCode = axiosError.response?.status;

    if (statusCode === 422 && Array.isArray(axiosError.response?.data?.detail)) {
      const validationErrors: Record<string, string[]> = {};
      for (const item of axiosError.response?.data?.detail ?? []) {
        const field = Array.isArray(item.loc) ? item.loc.slice(1).join('.') : 'detail';
        validationErrors[field] = [...(validationErrors[field] ?? []), item.msg];
      }
      return {
        message: 'Validation failed',
        statusCode,
        validationErrors,
      };
    }

    const detail = axiosError.response?.data?.detail;
    const message = typeof detail === 'string' ? detail : axiosError.message;
    return {
      message: message ?? 'Request failed',
      statusCode,
    };
  }

  if (error instanceof Error) {
    return { message: error.message };
  }

  return { message: 'An unknown error occurred' };
}
