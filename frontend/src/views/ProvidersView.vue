<template>
  <section class="providers-view">
    <div class="page-header">
      <div class="page-title">
        <h1>External Providers</h1>
        <p>Configure connectivity details for external Large Language Model providers.</p>
      </div>
      <button class="btn btn-primary" type="button" @click="openCreateModal">
        Add provider
      </button>
    </div>

    <div v-if="loading" class="loading-state">Loading providers…</div>

    <div v-else-if="providers.length === 0" class="empty-state">
      <div>
        <strong>No providers configured yet.</strong>
        <p>Add your first provider to start managing connectivity.</p>
      </div>
    </div>

    <ProviderTable
      v-else
      :providers="providers"
      :testing-id="testingId"
      :test-results="testResults"
      @edit="openEditModal"
      @delete="openDeleteDialog"
      @test="performTest"
    />

    <ProviderFormModal
      v-if="formVisible"
      :visible="formVisible"
      :mode="formMode"
      :provider="activeProvider"
      :busy="saving"
      :api-error="inlineFormError"
      :validation-errors="validationErrors"
      @close="closeForm"
      @submit="submitForm"
    />

    <ConfirmDialog
      :visible="!!pendingDelete"
      title="Remove provider"
      :message="pendingDelete ? `Are you sure you want to remove ${pendingDelete.name}? This action cannot be undone.` : ''"
      confirm-label="Delete"
      cancel-label="Cancel"
      :busy="deletingId === pendingDelete?.id"
      @confirm="confirmDelete"
      @cancel="confirmDialogClose"
    />

    <transition name="fade">
      <div v-if="successMessage" class="alert success" role="status">{{ successMessage }}</div>
    </transition>

    <transition name="fade">
      <div v-if="globalError" class="alert error" role="alert">{{ globalError }}</div>
    </transition>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import ProviderFormModal from '@/components/ProviderFormModal.vue';
import ProviderTable from '@/components/ProviderTable.vue';
import ConfirmDialog from '@/components/ConfirmDialog.vue';
import { useProviders } from '@/composables/useProviders';
import type { Provider, ProviderFormValues } from '@/types/providers';

const {
  providers,
  loading,
  saving,
  deletingId,
  testingId,
  error,
  successMessage,
  testResults,
  loadProviders,
  createProvider,
  updateProvider,
  deleteProvider,
  testProvider,
  clearFeedback,
} = useProviders();

const formVisible = ref(false);
const formMode = ref<'create' | 'edit'>('create');
const activeProvider = ref<Provider | null>(null);
const pendingDelete = ref<Provider | null>(null);

const validationErrors = ref<Record<string, string[]> | null>(null);

const globalError = computed(() => error.value?.message ?? null);
const inlineFormError = computed(() => (formVisible.value ? error.value?.message ?? null : null));

onMounted(() => {
  loadProviders();
});

watch(error, (next) => {
  validationErrors.value = next?.validationErrors ?? null;
});

const openCreateModal = () => {
  formMode.value = 'create';
  activeProvider.value = null;
  validationErrors.value = null;
  clearFeedback();
  formVisible.value = true;
};

const openEditModal = (provider: Provider) => {
  formMode.value = 'edit';
  activeProvider.value = provider;
  validationErrors.value = null;
  clearFeedback();
  formVisible.value = true;
};

const hideForm = (preserveFeedback = false) => {
  formVisible.value = false;
  activeProvider.value = null;
  validationErrors.value = null;
  if (!preserveFeedback) {
    clearFeedback();
  }
};

const closeForm = () => hideForm(false);

const submitForm = async (values: ProviderFormValues) => {
  try {
    if (formMode.value === 'create') {
      await createProvider(values);
    } else if (formMode.value === 'edit' && activeProvider.value) {
      await updateProvider(activeProvider.value.id, values);
    }
    if (!error.value) {
      hideForm(true);
    }
  } catch (err) {
    // error handled by composable
  }
};

const openDeleteDialog = (provider: Provider) => {
  pendingDelete.value = provider;
  clearFeedback();
};

const confirmDelete = async () => {
  if (!pendingDelete.value) return;
  try {
    await deleteProvider(pendingDelete.value.id);
    pendingDelete.value = null;
  } catch (err) {
    // handled via composable error state
  }
};

const confirmDialogClose = () => {
  pendingDelete.value = null;
  clearFeedback();
};

const performTest = async (provider: Provider) => {
  try {
    await testProvider(provider.id);
  } catch (err) {
    // error surfaced through global error banner
  }
};
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease-in-out;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
