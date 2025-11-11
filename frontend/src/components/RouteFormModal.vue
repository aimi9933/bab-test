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

interface Props {
  visible: boolean;
  mode: 'create' | 'edit';
  route: ModelRoute | null;
  busy?: boolean;
  apiError?: string | null;
  validationErrors?: Record<string, string[]> | null;
}

type FieldKey = 'name' | 'mode' | 'config';

const props = defineProps<Props>();

const emit = defineEmits<{
  (event: 'close'): void;
  (event: 'submit', values: ModelRouteFormValues): void;
}>();

const defaultFormValues = (): ModelRouteFormValues => ({
  name: '',
  mode: 'auto',
  config: {},
  isActive: true,
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
  resetErrors();
};

const resetErrors = () => {
  localErrors.name = null;
  localErrors.mode = null;
  localErrors.config = null;
};

const setFormFromRoute = (route: ModelRoute) => {
  form.name = route.name;
  form.mode = route.mode;
  form.config = route.config || {};
  form.isActive = route.isActive;
  configText.value = JSON.stringify(route.config || {}, null, 2);
  resetErrors();
};

watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      if (props.mode === 'edit' && props.route) {
        setFormFromRoute(props.route);
      } else {
        resetForm();
      }
    } else {
      resetForm();
    }
  },
  { immediate: true },
);

watch(
  () => props.route,
  (route) => {
    if (props.visible && props.mode === 'edit' && route) {
      setFormFromRoute(route);
    }
  },
);

const title = computed(() => (props.mode === 'edit' ? 'Edit route' : 'Add route'));
const subtitle = computed(() =>
  props.mode === 'edit'
    ? 'Update routing configuration and strategy settings.'
    : 'Configure routing strategy for API provider selection.',
);

const validateForm = (): boolean => {
  let valid = true;
  resetErrors();

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

  const sanitized: ModelRouteFormValues = {
    name: form.name.trim(),
    mode: form.mode,
    config: form.config,
    isActive: form.isActive,
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
</style>