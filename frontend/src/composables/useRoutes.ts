import { computed, reactive, ref } from 'vue';
import { api, toApiError } from '@/services/api';
import type { ApiError } from '@/services/api';
import type { ModelRoute, ModelRouteFormValues, RoutingSelectionResponse, RoutingStateResponse } from '@/types/routes';

export const useRoutes = () => {
  const routes = ref<ModelRoute[]>([]);
  const loading = ref(false);
  const saving = ref(false);
  const error = ref<ApiError | null>(null);
  const successMessage = ref<string | null>(null);
  const testResults = reactive<Record<number, RoutingSelectionResponse>>({});

  const resetFeedback = () => {
    error.value = null;
    successMessage.value = null;
  };

  const upsertRoute = (route: ModelRoute) => {
    const index = routes.value.findIndex((item) => item.id === route.id);
    if (index >= 0) {
      routes.value.splice(index, 1, route);
    } else {
      routes.value.unshift(route);
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

  const loadRoutes = async () => {
    loading.value = true;
    resetFeedback();
    try {
      routes.value = await api.listRoutes();
    } catch (err) {
      setError(toApiError(err));
    } finally {
      loading.value = false;
    }
  };

  const createRoute = async (values: ModelRouteFormValues) => {
    saving.value = true;
    resetFeedback();
    try {
      const route = await api.createRoute(values);
      upsertRoute(route);
      setSuccess('Route created successfully.');
      return route;
    } catch (err) {
      const apiError = toApiError(err);
      setError(apiError);
      throw apiError;
    } finally {
      saving.value = false;
    }
  };

  const updateRoute = async (id: number, values: ModelRouteFormValues) => {
    saving.value = true;
    resetFeedback();
    try {
      const route = await api.updateRoute(id, values);
      upsertRoute(route);
      setSuccess('Route updated successfully.');
      return route;
    } catch (err) {
      const apiError = toApiError(err);
      setError(apiError);
      throw apiError;
    } finally {
      saving.value = false;
    }
  };

  const deleteRoute = async (id: number) => {
    saving.value = true;
    resetFeedback();
    try {
      await api.deleteRoute(id);
      routes.value = routes.value.filter((route) => route.id !== id);
      delete testResults[id];
      setSuccess('Route removed.');
    } catch (err) {
      const apiError = toApiError(err);
      setError(apiError);
      throw apiError;
    } finally {
      saving.value = false;
    }
  };

  const testRouteSelection = async (id: number, model?: string) => {
    resetFeedback();
    try {
      const result = await api.selectProviderAndModel(id, model);
      testResults[id] = result;
      setSuccess(`Selected provider: ${result.providerName}, model: ${result.model}`);
      return result;
    } catch (err) {
      const apiError = toApiError(err);
      setError(apiError);
      throw apiError;
    }
  };

  const getRouteState = async (id: number) => {
    resetFeedback();
    try {
      const state = await api.getRouteState(id);
      return state;
    } catch (err) {
      const apiError = toApiError(err);
      setError(apiError);
      throw apiError;
    }
  };

  return {
    routes,
    loading,
    saving,
    error,
    successMessage,
    testResults,
    hasLoadedRoutes: computed(() => routes.value.length > 0),
    loadRoutes,
    createRoute,
    updateRoute,
    deleteRoute,
    testRouteSelection,
    getRouteState,
    clearFeedback: resetFeedback,
  };
};