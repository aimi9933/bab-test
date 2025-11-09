<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-backdrop" role="dialog" aria-modal="true" :aria-label="title">
      <div class="modal-panel" @click.stop>
        <header class="modal-header">
          <h2>{{ title }}</h2>
        </header>
        <div class="modal-body">
          <p>{{ message }}</p>
        </div>
        <footer class="modal-footer">
          <button class="btn btn-secondary" type="button" :disabled="busy" @click="$emit('cancel')">
            {{ cancelLabel }}
          </button>
          <button class="btn btn-danger" type="button" :disabled="busy" @click="$emit('confirm')">
            <span v-if="busy">Working…</span>
            <span v-else>{{ confirmLabel }}</span>
          </button>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
interface Props {
  visible: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  busy?: boolean;
}

defineProps<Props>();

defineEmits<{
  (event: 'confirm'): void;
  (event: 'cancel'): void;
}>();
</script>
