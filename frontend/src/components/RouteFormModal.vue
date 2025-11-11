<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-backdrop" role="dialog" aria-modal="true" :aria-label="title">
      <form class="modal-panel" @submit.prevent="handleSubmit">
        <header class="modal-header">
          <div>
            <h2>{{ title }}</h2>
            <p class="modal-subtitle">{{ subtitle }}</p>
          </div>
          <button class="btn btn-secondary" type="button" :disabled="busy" @click="$emit('close')">
            Close
          </button>
        </header>
        <div class="modal-body">
          <div v-if="apiError" class="alert error" role="alert">{{ apiError }}</div>

          <div class="field-group">
            <label for="route-name">Name</label>
            <input
              id="route-name"
              name="name"
              type="text"
              autocomplete="organization"
              :disabled="busy"
              v-model="form.name"
              placeholder="Main Route"
            />
            <p v-if="fieldError('name')" class="error-text">{{ fieldError('name') }}</p>
          </div>

          <div class="field-group">
            <label for="route-mode">Mode</label>
            <select
              id="route-mode"
              name="mode"
              :disabled="busy"
              v-model="form.mode"
            >
              <option value="auto">Auto - Cycle through providers</option>
              <option value="specific">Specific - Use single provider</option>
              <option value="multi">Multi - Multiple providers with priority</option>
            </select>
            <p v-if="fieldError('mode')" class="error-text">{{ fieldError('mode') }}</p>
            <div class="help-text">
              <div v-if="form.mode === 'auto'">
                <strong>Auto Mode:</strong> Select to cycle through multiple providers or use a specific one.
              </div>
              <div v-else-if="form.mode === 'specific'">
                <strong>Specific Mode:</strong> Select a single provider and choose which models to enable.
              </div>
              <div v-else-if="form.mode === 'multi'">
                <strong>Multi Mode:</strong> Add multiple providers with priorities and strategies.
              </div>
            </div>
          </div>

          <div class="field-group">
            <label class="switch">
              <input
                id="route-is-active"
                name="isActive"
                type="checkbox"
                :disabled="busy"
                v-model="form.isActive"
              />
              <span>{{ form.isActive ? 'Route is active' : 'Route is inactive' }}</span>
            </label>
          </div>

          <!-- Auto Mode: Provider Selection -->
          <div v-if="form.mode === 'auto'" class="field-group">
            <label for="auto-provider-mode">Provider Selection</label>
            <select
              id="auto-provider-mode"
              name="autoProviderMode"
              :disabled="busy || providersLoading"
              v-model="autoConfig.providerMode"
            >
              <option value="all">Use all enabled providers (cycle)</option>
              <option v-for="provider in availableProviders" :key="provider.id" :value="`provider_${provider.id}`">
                Use only {{ provider.name }}
              </option>
            </select>
          </div>

          <!-- Auto/Specific/Multi: Model Selection -->
          <div v-if="form.mode === 'auto' || form.mode === 'specific'" class="field-group">
            <div v-if="providersLoading && availableProviders.length === 0" class="loading-state">
              Loading providers...
            </div>
            <div v-else-if="currentProviderModels.length === 0" class="alert error">
              <span v-if="form.mode === 'auto'">
                Selected provider has no models. Please choose a different provider.
              </span>
              <span v-else>
                Selected provider has no models.
              </span>
            </div>
            <div v-else>
              <label>Models to enable</label>
              <div class="models-checklist">
                <div v-for="model in currentProviderModels" :key="model" class="checkbox-item">
                  <label>
                    <input
                      type="checkbox"
                      :value="model"
                      :checked="autoConfig.selectedModels.includes(model)"
                      :disabled="busy"
                      @change="toggleAutoModel(model)"
                    />
                    <span>{{ model }}</span>
                  </label>
                </div>
              </div>
              <p v-if="fieldError('models')" class="error-text">{{ fieldError('models') }}</p>
              <div v-if="autoConfig.selectedModels.length > 0" class="info-box">
                <strong>Strategy:</strong> 
                <span v-if="autoConfig.selectedModels.length === 1">
                  Single (fixed model: <code>{{ autoConfig.selectedModels[0] }}</code>)
                </span>
                <span v-else>
                  Cycle ({{ autoConfig.selectedModels.length }} models: <code>{{ autoConfig.selectedModels.join(', ') }}</code>)
                </span>
              </div>
            </div>
          </div>

          <!-- Specific Mode: Provider Selection -->
          <div v-if="form.mode === 'specific'" class="field-group">
            <label for="specific-provider">Select Provider</label>
            <select
              id="specific-provider"
              name="specificProvider"
              :disabled="busy || providersLoading"
              v-model="specificConfig.selectedProviderId"
            >
              <option :value="0">Select a provider</option>
              <option v-for="provider in availableProviders" :key="provider.id" :value="provider.id">
                {{ provider.name }}
              </option>
            </select>
            <p v-if="fieldError('provider')" class="error-text">{{ fieldError('provider') }}</p>
          </div>

          <!-- Multi Mode: Providers List -->
          <div v-if="form.mode === 'multi'" class="field-group">
            <label>Configure Providers</label>
            <div v-if="providersLoading && availableProviders.length === 0" class="loading-state">
              Loading providers...
            </div>
            <div v-else-if="availableProviders.length === 0" class="alert error">
              No API providers available. Please add a provider first before configuring routes.
            </div>
            <div v-else class="multi-providers-list">
              <div v-for="(providerConfig, index) in multiConfigs" :key="index" class="provider-config-item">
                <div class="provider-config-header">
                  <div class="field-group">
                    <label :for="`multi-provider-${index}`">Provider</label>
                    <select
                      :id="`multi-provider-${index}`"
                      :disabled="busy || providersLoading"
                      v-model="providerConfig.providerId"
                    >
                      <option :value="0">Select a provider</option>
                      <option v-for="provider in availableProviders" :key="provider.id" :value="provider.id">
                        {{ provider.name }}
                      </option>
                    </select>
                  </div>
                  <div class="field-group">
                    <label :for="`multi-strategy-${index}`">Strategy</label>
                    <select
                      :id="`multi-strategy-${index}`"
                      :disabled="busy"
                      v-model="providerConfig.strategy"
                    >
                      <option value="round-robin">Round Robin</option>
                      <option value="failover">Failover</option>
                    </select>
                  </div>
                  <div class="field-group">
                    <label :for="`multi-priority-${index}`">Priority</label>
                    <input
                      :id="`multi-priority-${index}`"
                      type="number"
                      min="0"
                      :disabled="busy"
                      v-model.number="providerConfig.priority"
                    />
                  </div>
                </div>
                <div v-if="getProviderModels(providerConfig.providerId).length > 0" class="provider-config-models">
                  <label>Models to enable</label>
                  <div class="models-checklist">
                    <div v-for="model in getProviderModels(providerConfig.providerId)" :key="model" class="checkbox-item">
                      <label>
                        <input
                          type="checkbox"
                          :value="model"
                          :checked="providerConfig.selectedModels.includes(model)"
                          :disabled="busy"
                          @change="toggleMultiModel(index, model)"
                        />
                        <span>{{ model }}</span>
                      </label>
                    </div>
                  </div>
                  <div v-if="providerConfig.selectedModels.length > 0" class="info-box">
                    <strong>Strategy:</strong> 
                    <span v-if="providerConfig.selectedModels.length === 1">
                      Single (fixed model: <code>{{ providerConfig.selectedModels[0] }}</code>)
                    </span>
                    <span v-else>
                      Cycle ({{ providerConfig.selectedModels.length }} models)
                    </span>
                  </div>
                </div>
                <div class="provider-config-actions">
                  <button
                    type="button"
                    class="btn btn-small btn-danger"
                    :disabled="busy || multiConfigs.length === 1"
                    @click="removeMultiProvider(index)"
                  >
                    Remove
                  </button>
                </div>
              </div>
              <button
                type="button"
                class="btn btn-secondary"
                :disabled="busy || availableProviders.length === 0"
                @click="addMultiProvider"
              >
                Add Provider
              </button>
            </div>
            <p v-if="fieldError('nodes')" class="error-text">{{ fieldError('nodes') }}</p>
          </div>
        </div>
        <footer class="modal-footer">
          <button class="btn btn-secondary" type="button" :disabled="busy" @click="$emit('close')">
            Cancel
          </button>
          <button class="btn btn-primary" type="submit" data-test="submit-button" :disabled="busy">
            <span v-if="busy">Saving…</span>
            <span v-else>{{ mode === 'edit' ? 'Save changes' : 'Create route' }}</span>
          </button>
        </footer>
      </form>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import type { ModelRoute, ModelRouteFormValues } from '@/types/routes';
import type { Provider } from '@/types/providers';
import { useProviders } from '@/composables/useProviders';

interface Props {
  visible: boolean;
  mode: 'create' | 'edit';
  route: ModelRoute | null;
  busy?: boolean;
  apiError?: string | null;
  validationErrors?: Record<string, string[]> | null;
}

type FieldKey = 'name' | 'mode' | 'models' | 'provider' | 'nodes';

const props = defineProps<Props>();

const { providers, loadProviders, loading: providersLoading } = useProviders();

const emit = defineEmits<{
  (event: 'close'): void;
  (event: 'submit', values: ModelRouteFormValues): void;
}>();

interface AutoConfig {
  providerMode: string;
  selectedModels: string[];
}

interface SpecificConfig {
  selectedProviderId: number;
  selectedModels: string[];
}

interface MultiProviderConfig {
  providerId: number;
  strategy: 'round-robin' | 'failover';
  priority: number;
  selectedModels: string[];
}

const defaultFormValues = (): ModelRouteFormValues => ({
  name: '',
  mode: 'auto',
  config: {},
  isActive: true,
  nodes: [],
});

const form = reactive<ModelRouteFormValues>(defaultFormValues());
const autoConfig = reactive<AutoConfig>({
  providerMode: 'all',
  selectedModels: [],
});
const specificConfig = reactive<SpecificConfig>({
  selectedProviderId: 0,
  selectedModels: [],
});
const multiConfigs = reactive<MultiProviderConfig[]>([]);

const localErrors = reactive<Record<FieldKey, string | null>>({
  name: null,
  mode: null,
  models: null,
  provider: null,
  nodes: null,
});

const resetForm = () => {
  Object.assign(form, defaultFormValues());
  autoConfig.providerMode = 'all';
  autoConfig.selectedModels = [];
  specificConfig.selectedProviderId = 0;
  specificConfig.selectedModels = [];
  multiConfigs.length = 0;
  resetLocalErrors();
};

const resetLocalErrors = () => {
  localErrors.name = null;
  localErrors.mode = null;
  localErrors.models = null;
  localErrors.provider = null;
  localErrors.nodes = null;
};

const getSelectedAutoProvider = (): Provider | null => {
  if (autoConfig.providerMode === 'all') {
    return null;
  }
  const providerId = parseInt(autoConfig.providerMode.replace('provider_', ''), 10);
  return providers.value.find(p => p.id === providerId) || null;
};

const currentProviderModels = computed(() => {
  if (form.mode === 'auto') {
    const provider = getSelectedAutoProvider();
    if (provider) {
      return provider.models || [];
    } else if (autoConfig.providerMode === 'all') {
      // When using all providers, aggregate models from all active providers
      const allModels = new Set<string>();
      providers.value.forEach(p => {
        if (p.isActive && p.models) {
          p.models.forEach(m => allModels.add(m));
        }
      });
      return Array.from(allModels).sort();
    }
    return [];
  } else if (form.mode === 'specific') {
    const provider = providers.value.find(p => p.id === specificConfig.selectedProviderId);
    return provider?.models || [];
  }
  return [];
});

const toggleAutoModel = (model: string) => {
  const index = autoConfig.selectedModels.indexOf(model);
  if (index > -1) {
    autoConfig.selectedModels.splice(index, 1);
  } else {
    autoConfig.selectedModels.push(model);
  }
};

const toggleMultiModel = (providerIndex: number, model: string) => {
  const config = multiConfigs[providerIndex];
  const index = config.selectedModels.indexOf(model);
  if (index > -1) {
    config.selectedModels.splice(index, 1);
  } else {
    config.selectedModels.push(model);
  }
};

const getProviderModels = (providerId: number): string[] => {
  const provider = providers.value.find(p => p.id === providerId);
  return provider?.models || [];
};

const addMultiProvider = () => {
  multiConfigs.push({
    providerId: 0,
    strategy: 'round-robin',
    priority: multiConfigs.length,
    selectedModels: [],
  });
};

const removeMultiProvider = (index: number) => {
  multiConfigs.splice(index, 1);
};

const setFormFromRoute = (route: ModelRoute) => {
  form.name = route.name;
  form.mode = route.mode;
  form.config = route.config || {};
  form.isActive = route.isActive;

  if (route.mode === 'auto') {
    const config = route.config as any || {};
    autoConfig.providerMode = config.providerMode || 'all';
    autoConfig.selectedModels = config.selectedModels || [];
  } else if (route.mode === 'specific') {
    if (route.nodes && route.nodes.length > 0) {
      specificConfig.selectedProviderId = route.nodes[0].apiId;
      specificConfig.selectedModels = route.nodes[0].models || [];
    }
  } else if (route.mode === 'multi') {
    multiConfigs.length = 0;
    if (route.nodes) {
      route.nodes.forEach(node => {
        multiConfigs.push({
          providerId: node.apiId,
          strategy: node.strategy,
          priority: node.priority,
          selectedModels: node.models || [],
        });
      });
    }
  }

  resetLocalErrors();
};

watch(
  () => props.visible,
  async (visible) => {
    if (visible) {
      await loadProviders();

      if (props.mode === 'edit' && props.route) {
        setFormFromRoute(props.route);
      } else {
        resetForm();
        if (form.mode === 'multi') {
          addMultiProvider();
        }
      }
    } else {
      resetForm();
    }
  },
  { immediate: true },
);

watch(
  () => props.route,
  async (route) => {
    if (props.visible && props.mode === 'edit' && route) {
      await loadProviders();
      setFormFromRoute(route);
    }
  },
);

watch(
  () => form.mode,
  (newMode) => {
    if (newMode === 'auto') {
      autoConfig.selectedModels = [];
    } else if (newMode === 'specific') {
      specificConfig.selectedModels = [];
    } else if (newMode === 'multi') {
      multiConfigs.length = 0;
      addMultiProvider();
    }
  },
);

const availableProviders = computed(() => providers.value);

const title = computed(() => (props.mode === 'edit' ? 'Edit route' : 'Add route'));
const subtitle = computed(() =>
  props.mode === 'edit'
    ? 'Update routing configuration and strategy settings.'
    : 'Configure routing strategy for API provider selection.',
);

const validateForm = (): boolean => {
  let valid = true;
  resetLocalErrors();

  if (!form.name.trim()) {
    localErrors.name = 'Route name is required';
    valid = false;
  }

  if (!form.mode) {
    localErrors.mode = 'Routing mode is required';
    valid = false;
  }

  if (form.mode === 'auto') {
    if (autoConfig.selectedModels.length === 0) {
      localErrors.models = 'At least one model must be enabled';
      valid = false;
    }
  } else if (form.mode === 'specific') {
    if (!specificConfig.selectedProviderId) {
      localErrors.provider = 'A provider must be selected';
      valid = false;
    }
    if (specificConfig.selectedModels.length === 0) {
      localErrors.models = 'At least one model must be enabled';
      valid = false;
    }
  } else if (form.mode === 'multi') {
    if (multiConfigs.length === 0) {
      localErrors.nodes = 'At least one provider must be added';
      valid = false;
    }
    for (let i = 0; i < multiConfigs.length; i++) {
      const config = multiConfigs[i];
      if (!config.providerId) {
        localErrors.nodes = `Provider ${i + 1}: A provider must be selected`;
        valid = false;
        break;
      }
      if (config.selectedModels.length === 0) {
        localErrors.nodes = `Provider ${i + 1}: At least one model must be enabled`;
        valid = false;
        break;
      }
    }
  }

  return valid;
};

const toSnakeCase = (value: string) => value.replace(/[A-Z]/g, (match) => `_${match.toLowerCase()}`);

const validationMessage = (field: FieldKey): string | null => {
  if (!props.validationErrors) {
    return null;
  }

  const fieldVariants = [field, toSnakeCase(field)];
  const matches: string[] = [];

  for (const [key, messages] of Object.entries(props.validationErrors)) {
    for (const variant of fieldVariants) {
      if (key === variant || key.endsWith(`.${variant}`) || key.includes(variant)) {
        matches.push(...messages);
        break;
      }
    }
  }

  if (matches.length === 0) {
    return null;
  }

  return matches.join(' ');
};

const fieldError = (field: FieldKey) => localErrors[field] ?? validationMessage(field);

const handleSubmit = () => {
  if (!validateForm()) {
    return;
  }

  let nodes = [];
  let config: Record<string, any> = {};

  if (form.mode === 'auto') {
    config = {
      providerMode: autoConfig.providerMode,
      selectedModels: autoConfig.selectedModels,
      modelStrategy: autoConfig.selectedModels.length === 1 ? 'single' : 'cycle',
    };
  } else if (form.mode === 'specific') {
    config = {
      selectedModels: specificConfig.selectedModels,
      modelStrategy: specificConfig.selectedModels.length === 1 ? 'single' : 'cycle',
    };
    nodes = [
      {
        apiId: specificConfig.selectedProviderId,
        models: specificConfig.selectedModels,
        strategy: 'round-robin',
        priority: 0,
      },
    ];
  } else if (form.mode === 'multi') {
    nodes = multiConfigs.map(config => ({
      apiId: config.providerId,
      models: config.selectedModels,
      strategy: config.strategy,
      priority: config.priority,
    }));
  }

  const sanitized: ModelRouteFormValues = {
    name: form.name.trim(),
    mode: form.mode,
    config,
    isActive: form.isActive,
    nodes,
  };

  emit('submit', sanitized);
};
</script>

<style scoped>
.help-text {
  font-size: 0.875rem;
  color: #6c757d;
  margin-top: 0.5rem;
}

.help-text div {
  margin-bottom: 0.25rem;
}

.nodes-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.node-item {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1rem;
  background: #f8fafc;
}

.node-actions {
  margin-top: 0.5rem;
  text-align: right;
}

textarea {
  width: 100%;
  min-height: 80px;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.875rem;
  resize: vertical;
}

textarea:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: white;
  font-size: 0.875rem;
}

select:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.loading-state {
  padding: 1rem;
  text-align: center;
  color: #6c757d;
  font-style: italic;
}

.models-checklist {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.checkbox-item {
  display: flex;
  align-items: center;
}

.checkbox-item label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  margin: 0;
}

.checkbox-item input[type="checkbox"] {
  cursor: pointer;
  width: 18px;
  height: 18px;
}

.info-box {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background-color: #e0f2fe;
  border-left: 3px solid #0284c7;
  border-radius: 4px;
  font-size: 0.875rem;
  color: #0c4a6e;
}

.info-box code {
  background-color: rgba(2, 132, 199, 0.1);
  padding: 0.2rem 0.4rem;
  border-radius: 2px;
  font-family: monospace;
  font-size: 0.8rem;
}

.multi-providers-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.provider-config-item {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1rem;
  background: #f8fafc;
}

.provider-config-header {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.provider-config-models {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.provider-config-actions {
  margin-top: 1rem;
  text-align: right;
}

.field-inline {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 1rem;
}
</style>