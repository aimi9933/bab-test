<template>
  <section class="routes-view">
    <div class="page-header">
      <div class="page-title">
        <h1>Model Routes</h1>
        <p>Configure routing strategies for API provider selection and model distribution.</p>
      </div>
      <button class="btn btn-primary" type="button" @click="openCreateModal">
        Add route
      </button>
    </div>

    <div v-if="loading" class="loading-state">Loading routes…</div>

    <div v-else-if="routes.length === 0" class="empty-state">
      <div>
        <strong>No routes configured yet.</strong>
        <p>Add your first route to start managing API provider routing.</p>
      </div>
    </div>

    <RoutesTable
      v-else
      :routes="routes"
      :testing-id="testingId"
      :test-results="testResults"
      @edit="openEditModal"
      @delete="openDeleteDialog"
      @test="performTest"
      @state="showState"
    />

    <RouteFormModal
      v-if="formVisible"
      :visible="formVisible"
      :mode="formMode"
      :route="activeRoute"
      :busy="saving"
      :api-error="inlineFormError"
      :validation-errors="validationErrors"
      @close="closeForm"
      @submit="submitForm"
    />

    <ConfirmDialog
      :visible="!!pendingDelete"
      title="Remove route"
      :message="pendingDelete ? `Are you sure you want to remove ${pendingDelete.name}? This action cannot be undone.` : ''"
      confirm-label="Delete"
      cancel-label="Cancel"
      :busy="deletingId === pendingDelete?.id"
      @confirm="confirmDelete"
      @cancel="confirmDialogClose"
    />

    <RouteStateModal
      v-if="stateModalVisible"
      :visible="stateModalVisible"
      :route-state="routeState"
      @close="closeStateModal"
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
import RouteFormModal from '@/components/RouteFormModal.vue';
import RoutesTable from '@/components/RoutesTable.vue';
import RouteStateModal from '@/components/RouteStateModal.vue';
import ConfirmDialog from '@/components/ConfirmDialog.vue';
import { useRoutes } from '@/composables/useRoutes';
import type { ModelRoute, ModelRouteFormValues, RoutingStateResponse } from '@/types/routes';

const {
  routes,
  loading,
  saving,
  error,
  successMessage,
  testResults,
  loadRoutes,
  createRoute,
  updateRoute,
  deleteRoute,
  testRouteSelection,
  getRouteState,
  clearFeedback,
} = useRoutes();

const formVisible = ref(false);
const formMode = ref<'create' | 'edit'>('create');
const activeRoute = ref<ModelRoute | null>(null);
const pendingDelete = ref<ModelRoute | null>(null);
const testingId = ref<number | null>(null);
const deletingId = ref<number | null>(null);
const validationErrors = ref<Record<string, string[]> | null>(null);
const stateModalVisible = ref(false);
const routeState = ref<RoutingStateResponse | null>(null);

const globalError = computed(() => error.value?.message ?? null);
const inlineFormError = computed(() => (formVisible.value ? error.value?.message ?? null : null));

onMounted(() => {
  loadRoutes();
});

watch(error, (next) => {
  validationErrors.value = next?.validationErrors ?? null;
});

const openCreateModal = () => {
  formMode.value = 'create';
  activeRoute.value = null;
  validationErrors.value = null;
  clearFeedback();
  formVisible.value = true;
};

const openEditModal = (route: ModelRoute) => {
  formMode.value = 'edit';
  activeRoute.value = route;
  validationErrors.value = null;
  clearFeedback();
  formVisible.value = true;
};

const hideForm = (preserveFeedback = false) => {
  formVisible.value = false;
  activeRoute.value = null;
  validationErrors.value = null;
  if (!preserveFeedback) {
    clearFeedback();
  }
};

const closeForm = () => hideForm(false);

const submitForm = async (values: ModelRouteFormValues) => {
  try {
    if (formMode.value === 'create') {
      await createRoute(values);
    } else if (formMode.value === 'edit' && activeRoute.value) {
      await updateRoute(activeRoute.value.id, values);
    }
    if (!error.value) {
      hideForm(true);
    }
  } catch (err) {
    // error handled by composable
  }
};

const openDeleteDialog = (route: ModelRoute) => {
  pendingDelete.value = route;
  clearFeedback();
};

const confirmDelete = async () => {
  if (!pendingDelete.value) return;
  try {
    deletingId.value = pendingDelete.value.id;
    await deleteRoute(pendingDelete.value.id);
    pendingDelete.value = null;
  } catch (err) {
    // handled via composable error state
  } finally {
    deletingId.value = null;
  }
};

const confirmDialogClose = () => {
  pendingDelete.value = null;
  clearFeedback();
};

const performTest = async (route: ModelRoute) => {
  try {
    testingId.value = route.id;
    await testRouteSelection(route.id);
  } catch (err) {
    // error surfaced through global error banner
  } finally {
    testingId.value = null;
  }
};

const showState = async (route: ModelRoute) => {
  try {
    routeState.value = await getRouteState(route.id);
    stateModalVisible.value = true;
  } catch (err) {
    // error surfaced through global error banner
  }
};

const closeStateModal = () => {
  stateModalVisible.value = false;
  routeState.value = null;
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