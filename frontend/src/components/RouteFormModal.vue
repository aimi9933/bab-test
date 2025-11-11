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
              <option value="auto">Auto - Round-robin through all providers</option>
              <option value="specific">Specific - Use provider based on model hint</option>
              <option value="multi">Multi - Priority-based with failover</option>
            </select>
            <p v-if="fieldError('mode')" class="error-text">{{ fieldError('mode') }}</p>
            <div class="help-text">
              <div v-if="form.mode === 'auto'">
                <strong>Auto Mode:</strong> Automatically cycles through all available providers using round-robin algorithm.
              </div>
              <div v-else-if="form.mode === 'specific'">
                <strong>Specific Mode:</strong> Selects provider based on the model hint provided in the request.
              </div>
              <div v-else-if="form.mode === 'multi'">
                <strong>Multi Mode:</strong> Uses priority-based routing with failover strategies.
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

          <div v-if="form.mode === 'multi'" class="field-group">
            <label>Configuration (Optional)</label>
            <textarea
              name="config"
              :disabled="busy"
              v-model="configText"
              placeholder='{"default_strategy": "round-robin"}'
              rows="4"
            ></textarea>
            <p v-if="fieldError('config')" class="error-text">{{ fieldError('config') }}</p>
            <p class="help-text">
              JSON configuration for multi-mode routing (optional).
            </p>
          </div>

          <div v-if="form.mode === 'specific' || form.mode === 'multi'" class="field-group">
            <label>Provider Nodes</label>
            <div v-if="providersLoading && availableProviders.length === 0" class="loading-state">
              Loading providers...
            </div>
            <div v-else-if="availableProviders.length === 0" class="alert error">
              No API providers available. Please add a provider first before configuring routes.
            </div>
            <div v-else class="nodes-list">
              <div v-for="(node, index) in form.nodes" :key="index" class="node-item">
                <div class="field-inline">
                  <div class="field-group">
                    <label :for="`node-api-${index}`">Provider</label>
                    <select
                      :id="`node-api-${index}`"
                      :name="`node-api-${index}`"
                      :disabled="busy || providersLoading"
                      v-model="node.apiId"
                    >
                      <option value="">Select a provider</option>
                      <option v-for="provider in availableProviders" :key="provider.id" :value="provider.id">
                        {{ provider.name }}
                      </option>
                    </select>
                  </div>
                  <div class="field-group">
                    <label :for="`node-models-${index}`">Models (comma-separated)</label>
                    <input
                      :id="`node-models-${index}`"
                      :name="`node-models-${index}`"
                      type="text"
                      :disabled="busy"
                      v-model="node.modelsText"
                      placeholder="gpt-4, gpt-3.5-turbo"
                    />
                  </div>
                  <div class="field-group">
                    <label :for="`node-strategy-${index}`">Strategy</label>
                    <select
                      :id="`node-strategy-${index}`"
                      :name="`node-strategy-${index}`"
                      :disabled="busy"
                      v-model="node.strategy"
                    >
                      <option value="round-robin">Round Robin</option>
                      <option value="failover">Failover</option>
                    </select>
                  </div>
                  <div class="field-group">
                    <label :for="`node-priority-${index}`">Priority</label>
                    <input
                      :id="`node-priority-${index}`"
                      :name="`node-priority-${index}`"
                      type="number"
                      min="0"
                      :disabled="busy"
                      v-model="node.priority"
                    />
                  </div>
                </div>
                <div class="node-actions">
                  <button
                    type="button"
                    class="btn btn-small btn-danger"
                    :disabled="busy || form.nodes.length === 1"
                    @click="removeNode(index)"
                  >
                    Remove
                  </button>
                </div>
              </div>
              <button
                type="button"
                class="btn btn-secondary"
                :disabled="busy || availableProviders.length === 0"
                @click="addNode"
              >
                Add Provider Node
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

type FieldKey = 'name' | 'mode' | 'config' | 'nodes';

const props = defineProps<Props>();

const { providers, loadProviders, loading: providersLoading } = useProviders();

const emit = defineEmits<{
  (event: 'close'): void;
  (event: 'submit', values: ModelRouteFormValues): void;
}>();

interface RouteNodeForm {
  apiId: number;
  modelsText: string;
  strategy: 'round-robin' | 'failover';
  priority: number;
}

const defaultFormValues = (): ModelRouteFormValues => ({
  name: '',
  mode: 'auto',
  config: {},
  isActive: true,
  nodes: [],
});

const form = reactive<ModelRouteFormValues>(defaultFormValues());
const configText = ref('');

const localErrors = reactive<Record<FieldKey, string | null>>({
  name: null,
  mode: null,
  config: null,
});

const resetForm = () => {
  Object.assign(form, defaultFormValues());
  configText.value = '';
  resetLocalErrors();
};

const resetLocalErrors = () => {
  localErrors.name = null;
  localErrors.mode = null;
  localErrors.config = null;
  localErrors.nodes = null;
};

const addNode = () => {
  form.nodes.push({
    apiId: 0,
    modelsText: '',
    strategy: 'round-robin',
    priority: form.nodes.length,
  });
};

const removeNode = (index: number) => {
  form.nodes.splice(index, 1);
};

const setFormFromRoute = (route: ModelRoute) => {
  form.name = route.name;
  form.mode = route.mode;
  form.config = route.config || {};
  form.isActive = route.isActive;
  form.nodes = route.nodes.map(node => ({
    apiId: node.apiId,
    modelsText: node.models.join(', '),
    strategy: node.strategy,
    priority: node.priority,
  }));
  configText.value = JSON.stringify(route.config || {}, null, 2);
  resetErrors();
};

watch(
  () => props.visible,
  async (visible) => {
    if (visible) {
      // Ensure providers are loaded when the modal opens
      await loadProviders();
      
      if (props.mode === 'edit' && props.route) {
        setFormFromRoute(props.route);
      } else {
        resetForm();
        // Add a default node for specific/multi modes
        if (form.mode === 'specific' || form.mode === 'multi') {
          addNode();
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
  (newMode, oldMode) => {
    // Add a default node when switching to specific/multi mode from auto
    if ((newMode === 'specific' || newMode === 'multi') && 
        (oldMode === 'auto' || oldMode === undefined) && 
        form.nodes.length === 0) {
      addNode();
    }
    // Clear nodes when switching to auto mode
    if (newMode === 'auto' && form.nodes.length > 0) {
      form.nodes = [];
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

  // Validate config JSON if provided
  if (form.mode === 'multi' && configText.value.trim()) {
    try {
      form.config = JSON.parse(configText.value);
    } catch (error) {
      localErrors.config = 'Invalid JSON configuration';
      valid = false;
    }
  } else {
    form.config = {};
  }

  // Validate nodes for specific and multi modes
  if ((form.mode === 'specific' || form.mode === 'multi') && form.nodes.length === 0) {
    localErrors.nodes = 'At least one provider node is required for specific/multi modes';
    valid = false;
  }

  // Validate each node
  for (let i = 0; i < form.nodes.length; i++) {
    const node = form.nodes[i];
    if (!node.apiId) {
      localErrors.nodes = `Node ${i + 1}: Provider is required`;
      valid = false;
      break;
    }
    if (node.modelsText.trim()) {
      const models = node.modelsText.split(',').map(m => m.trim()).filter(m => m.length > 0);
      if (models.length === 0) {
        localErrors.nodes = `Node ${i + 1}: At least one model is required`;
        valid = false;
        break;
      }
      node.models = models;
    } else {
      localErrors.nodes = `Node ${i + 1}: Models are required`;
      valid = false;
      break;
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

  // Convert form nodes to backend format (only for specific/multi modes)
  let nodes = [];
  if (form.mode === 'specific' || form.mode === 'multi') {
    nodes = form.nodes.map(node => ({
      apiId: node.apiId,
      models: node.modelsText.split(',').map(m => m.trim()).filter(m => m.length > 0),
      strategy: node.strategy,
      priority: node.priority,
    }));
  }

  const sanitized: ModelRouteFormValues = {
    name: form.name.trim(),
    mode: form.mode,
    config: form.config,
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
</style>