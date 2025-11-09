import { computed, reactive, ref } from 'vue';
import { api, toApiError } from '@/services/api';
import type { ApiError } from '@/services/api';
import type { Provider, ProviderFormValues, ProviderTestResult } from '@/types/providers';
import type { ProviderCreatePayload, ProviderUpdatePayload } from '@/types/providers';

const normalizeModels = (models: string[]): string[] => {
  return models.map((model) => model.trim()).filter((model) => model.length > 0);
};

const toCreatePayload = (values: ProviderFormValues): ProviderCreatePayload => ({
  name: values.name.trim(),
  base_url: values.baseUrl.trim(),
  models: normalizeModels(values.models),
  is_active: values.isActive,
  api_key: values.apiKey.trim(),
});

const toUpdatePayload = (values: ProviderFormValues): ProviderUpdatePayload => {
  const payload: ProviderUpdatePayload = {
    name: values.name.trim(),
    base_url: values.baseUrl.trim(),
    models: normalizeModels(values.models),
    is_active: values.isActive,
  };

  if (values.apiKey.trim()) {
    payload.api_key = values.apiKey.trim();
  }

  return payload;
};

export const useProviders = () => {
  const providers = ref<Provider[]>([]);
  const loading = ref(false);
  const saving = ref(false);
  const testingId = ref<number | null>(null);
  const deletingId = ref<number | null>(null);
  const error = ref<ApiError | null>(null);
  const successMessage = ref<string | null>(null);
  const testResults = reactive<Record<number, ProviderTestResult>>({});

  const resetFeedback = () => {
    error.value = null;
    successMessage.value = null;
  };

  const upsertProvider = (provider: Provider) => {
    const index = providers.value.findIndex((item) => item.id === provider.id);
    if (index >= 0) {
      providers.value.splice(index, 1, provider);
    } else {
      providers.value.unshift(provider);
    }
  };

  const setError = (apiError: ApiError) => {
    error.value = apiError;
    successMessage.value = null;
  };

  const setSuccess = (message: string) => {
    successMessage.value = message;
    error.value = null;
  };

  const loadProviders = async () => {
    loading.value = true;
    resetFeedback();
    try {
      providers.value = await api.listProviders();
    } catch (err) {
      setError(toApiError(err));
    } finally {
      loading.value = false;
    }
  };

  const createProvider = async (values: ProviderFormValues) => {
    saving.value = true;
    resetFeedback();
    try {
      const provider = await api.createProvider(toCreatePayload(values));
      upsertProvider(provider);
      setSuccess('Provider created successfully.');
      return provider;
    } catch (err) {
      const apiError = toApiError(err);
      setError(apiError);
      throw apiError;
    } finally {
      saving.value = false;
    }
  };

  const updateProvider = async (id: number, values: ProviderFormValues) => {
    saving.value = true;
    resetFeedback();
    try {
      const provider = await api.updateProvider(id, toUpdatePayload(values));
      upsertProvider(provider);
      setSuccess('Provider updated successfully.');
      return provider;
    } catch (err) {
      const apiError = toApiError(err);
      setError(apiError);
      throw apiError;
    } finally {
      saving.value = false;
    }
  };

  const deleteProvider = async (id: number) => {
    deletingId.value = id;
    resetFeedback();
    try {
      await api.deleteProvider(id);
      providers.value = providers.value.filter((provider) => provider.id !== id);
      delete testResults[id];
      setSuccess('Provider removed.');
    } catch (err) {
      const apiError = toApiError(err);
      setError(apiError);
      throw apiError;
    } finally {
      deletingId.value = null;
    }
  };

  const testProvider = async (id: number, timeoutSeconds?: number) => {
    testingId.value = id;
    resetFeedback();
    try {
      const result = await api.testProvider(id, timeoutSeconds);
      testResults[id] = result;
      providers.value = providers.value.map((provider) =>
        provider.id === id
          ? {
              ...provider,
              status: result.status,
              latencyMs: result.latencyMs,
              lastTestedAt: result.completedAt,
            }
          : provider,
      );
      setSuccess('Test completed.');
      return result;
    } catch (err) {
      const apiError = toApiError(err);
      setError(apiError);
      throw apiError;
    } finally {
      testingId.value = null;
    }
  };

  return {
    providers,
    loading,
    saving,
    testingId,
    deletingId,
    error,
    successMessage,
    testResults,
    hasLoadedProviders: computed(() => providers.value.length > 0),
    loadProviders,
    createProvider,
    updateProvider,
    deleteProvider,
    testProvider,
    clearFeedback: resetFeedback,
  };
};

export { normalizeModels };
