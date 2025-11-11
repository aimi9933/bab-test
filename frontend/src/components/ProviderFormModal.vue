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
            <label for="provider-name">Name</label>
            <input
              id="provider-name"
              name="name"
              type="text"
              autocomplete="organization"
              :disabled="busy"
              v-model="form.name"
              placeholder="Acme AI"
            />
            <p v-if="fieldError('name')" class="error-text">{{ fieldError('name') }}</p>
          </div>

          <div class="field-group">
            <label for="provider-base-url">Base URL</label>
            <input
              id="provider-base-url"
              name="baseUrl"
              type="url"
              autocomplete="url"
              :disabled="busy"
              v-model="form.baseUrl"
              placeholder="https://api.example.com/v1"
            />
            <p v-if="fieldError('baseUrl')" class="error-text">{{ fieldError('baseUrl') }}</p>
          </div>

          <div class="field-group">
            <label>Available models</label>
            <div class="field-group">
              <div v-for="(model, index) in form.models" :key="index" class="field-inline">
                <input
                  :name="`model-${index}`"
                  type="text"
                  :disabled="busy"
                  v-model="form.models[index]"
                  placeholder="gpt-4"
                />
                <button
                  type="button"
                  class="btn btn-secondary"
                  data-test="remove-model"
                  :disabled="busy || form.models.length === 1"
                  @click="removeModel(index)"
                >
                  Remove
                </button>
              </div>
            </div>
            <div class="field-inline">
              <button
                type="button"
                class="btn btn-secondary"
                data-test="add-model"
                :disabled="busy"
                @click="addModel"
              >
                Add model
              </button>
            </div>
            <p v-if="fieldError('models')" class="error-text">{{ fieldError('models') }}</p>
          </div>

          <div class="field-group">
            <label for="provider-api-key">API key</label>
            <div v-if="mode === 'edit' && provider?.apiKeyMasked && !apiKeyInputVisible" class="masked-key-display">
              <span class="masked-key">{{ provider.apiKeyMasked }}</span>
              <button type="button" class="btn btn-small btn-secondary" @click="showApiKeyInput" :disabled="busy">
                Update
              </button>
            </div>
            <input
              v-else
              id="provider-api-key"
              name="apiKey"
              type="password"
              autocomplete="off"
              :disabled="busy"
              v-model="form.apiKey"
              :placeholder="mode === 'edit' ? 'Enter new API key or leave blank to keep existing' : 'sk-live-***'"
            />
            <p v-if="fieldError('apiKey')" class="error-text">{{ fieldError('apiKey') }}</p>
            <p v-if="mode === 'edit' && provider?.apiKeyMasked && !apiKeyInputVisible" class="help-text">
              API key is saved and masked for security. Click "Update" to change it.
            </p>
          </div>

          <div class="field-group">
            <label class="switch">
              <input
                id="provider-is-active"
                name="isActive"
                type="checkbox"
                :disabled="busy"
                v-model="form.isActive"
              />
              <span>{{ form.isActive ? 'Provider is active' : 'Provider is inactive' }}</span>
            </label>
          </div>
        </div>
        <footer class="modal-footer">
          <button class="btn btn-secondary" type="button" :disabled="busy" @click="$emit('close')">
            Cancel
          </button>
          <button class="btn btn-primary" type="submit" data-test="submit-button" :disabled="busy">
            <span v-if="busy">Saving…</span>
            <span v-else>{{ mode === 'edit' ? 'Save changes' : 'Create provider' }}</span>
          </button>
        </footer>
      </form>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import { normalizeModels } from '@/composables/useProviders';
import type { Provider, ProviderFormValues } from '@/types/providers';

interface Props {
  visible: boolean;
  mode: 'create' | 'edit';
  provider: Provider | null;
  busy?: boolean;
  apiError?: string | null;
  validationErrors?: Record<string, string[]> | null;
}

type FieldKey = 'name' | 'baseUrl' | 'models' | 'apiKey';

const props = defineProps<Props>();

const emit = defineEmits<{
  (event: 'close'): void;
  (event: 'submit', values: ProviderFormValues): void;
}>();

const defaultFormValues = (): ProviderFormValues => ({
  name: '',
  baseUrl: '',
  models: [''],
  isActive: true,
  apiKey: '',
});

const form = reactive<ProviderFormValues>(defaultFormValues());
const apiKeyInputVisible = ref(false);

const localErrors = reactive<Record<FieldKey, string | null>>({
  name: null,
  baseUrl: null,
  models: null,
  apiKey: null,
});

const resetForm = () => {
  Object.assign(form, defaultFormValues());
  apiKeyInputVisible.value = false;
  resetErrors();
};

const resetErrors = () => {
  localErrors.name = null;
  localErrors.baseUrl = null;
  localErrors.models = null;
  localErrors.apiKey = null;
};

const setFormFromProvider = (provider: Provider) => {
  form.name = provider.name;
  form.baseUrl = provider.baseUrl;
  form.models = provider.models.length > 0 ? [...provider.models] : [''];
  form.isActive = provider.isActive;
  form.apiKey = ''; // Always start with empty to show masked key
  apiKeyInputVisible.value = false; // Hide API key input initially
  resetErrors();
};

const showApiKeyInput = () => {
  form.apiKey = ''; // Clear to show input field
  apiKeyInputVisible.value = true; // Show the input field
};

watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      if (props.mode === 'edit' && props.provider) {
        setFormFromProvider(props.provider);
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
  () => props.provider,
  (provider) => {
    if (props.visible && props.mode === 'edit' && provider) {
      setFormFromProvider(provider);
    }
  },
);

const title = computed(() => (props.mode === 'edit' ? 'Edit provider' : 'Add provider'));
const subtitle = computed(() =>
  props.mode === 'edit'
    ? 'Update connection details and availability settings.'
    : 'Provide connection details for the external API provider.',
);

const addModel = () => {
  form.models = [...form.models, ''];
};

const removeModel = (index: number) => {
  if (form.models.length === 1) {
    form.models.splice(0, 1, '');
    return;
  }
  form.models.splice(index, 1);
};

const validateForm = (): boolean => {
  let valid = true;
  resetErrors();

  if (!form.name.trim()) {
    localErrors.name = 'Provider name is required';
    valid = false;
  }

  try {
    const parsed = form.baseUrl.trim();
    if (!parsed) {
      throw new Error('Base URL is required');
    }
    // Throws if invalid
    new URL(parsed);
  } catch (error) {
    localErrors.baseUrl = 'A valid URL is required';
    valid = false;
  }

  const models = normalizeModels(form.models);
  if (models.length === 0) {
    localErrors.models = 'Specify at least one model identifier';
    valid = false;
  }

  // For create mode, API key is always required
  if (props.mode === 'create' && !form.apiKey.trim()) {
    localErrors.apiKey = 'API key is required';
    valid = false;
  }

  // For edit mode, API key is only required if the input field is visible
  // (i.e., user clicked "Update" to change it)
  if (props.mode === 'edit' && apiKeyInputVisible.value && !form.apiKey.trim()) {
    // Input is visible but empty - user wants to update with empty key
    localErrors.apiKey = 'API key is required when updating';
    valid = false;
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

  const sanitized: ProviderFormValues = {
    name: form.name.trim(),
    baseUrl: form.baseUrl.trim(),
    models: normalizeModels(form.models),
    isActive: form.isActive,
    apiKey: form.apiKey.trim(),
  };

  emit('submit', sanitized);
};
</script>

<style scoped>
.masked-key-display {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9rem;
}

.masked-key {
  color: #6c757d;
  flex: 1;
}

.help-text {
  font-size: 0.875rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

.btn-small {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}
</style>
