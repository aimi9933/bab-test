export interface ProviderResponse {
  id: number;
  name: string;
  base_url: string;
  models: string[];
  is_active: boolean;
  status: string;
  latency_ms: number | null;
  last_tested_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface Provider {
  id: number;
  name: string;
  baseUrl: string;
  models: string[];
  isActive: boolean;
  status: string;
  latencyMs: number | null;
  lastTestedAt: string | null;
  createdAt: string | null;
  updatedAt: string | null;
}

export interface ProviderFormValues {
  name: string;
  baseUrl: string;
  models: string[];
  isActive: boolean;
  apiKey: string;
}

export interface ProviderCreatePayload {
  name: string;
  base_url: string;
  models: string[];
  is_active: boolean;
  api_key: string;
}

export interface ProviderUpdatePayload {
  name?: string;
  base_url?: string;
  models?: string[];
  is_active?: boolean;
  api_key?: string;
}

export interface ProviderTestResult {
  status: string;
  statusCode: number | null;
  latencyMs: number | null;
  detail: string | null;
  completedAt: string;
}
