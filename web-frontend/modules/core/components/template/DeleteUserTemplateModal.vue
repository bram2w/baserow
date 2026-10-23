<template>
  <Modal
    ref="modal"
    class="user-template-modal-wrapper user-template-modal-wrapper--small"
    :box-padding="false"
    :close-button="false"
    @hidden="emit('hidden')"
  >
    <div class="user-template-modal">
      <div class="user-template-modal__head">
        <h2 class="user-template-modal__title">
          {{ $t('deleteUserTemplateModal.title', { name: template.name }) }}
        </h2>
        <button
          type="button"
          class="user-template-modal__head-action user-template-modal__close"
          :title="$t('action.close')"
          @click="hide()"
        >
          <i class="iconoir-cancel"></i>
        </button>
      </div>

      <div class="user-template-modal__body">
        <p class="user-template-modal__description margin-bottom-0">
          {{ $t('deleteUserTemplateModal.description') }}
        </p>
      </div>

      <div class="user-template-modal__footer">
        <div class="user-template-modal__footer-actions">
          <Button type="secondary" @click="hide()">
            {{ $t('action.cancel') }}
          </Button>
          <Button
            type="danger"
            :loading="loading"
            :disabled="loading"
            @click="confirm"
          >
            {{ $t('deleteUserTemplateModal.delete') }}
          </Button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useNuxtApp } from '#app'

import TemplateService from '@baserow/modules/core/services/template'
import { notifyIf } from '@baserow/modules/core/utils/error'

/**
 * Asks the author to confirm that their template is deleted, then deletes it. The
 * deletion can't be undone.
 */
const props = defineProps({
  // The user's template as listed in their templates.
  template: {
    type: Object,
    required: true,
  },
})

// `deleted` is emitted with the id of the deleted template, also when the modal was
// closed or opened for another template while the request ran, whether it was
// already deleted, for example in another tab, and the `performance.now()` at which
// the deletion was requested.
const emit = defineEmits(['deleted', 'hidden'])

const { $client } = useNuxtApp()

const modal = ref(null)
// The ids of the templates whose deletion request runs.
const pending = reactive(new Set())

const loading = computed(() => pending.has(props.template.id))

function show(...args) {
  modal.value.show(...args)
}

function hide(...args) {
  modal.value.hide(...args)
}

function deleted(id, alreadyDeleted, requestedAt) {
  emit('deleted', id, alreadyDeleted, requestedAt)
  if (props.template.id === id) {
    hide()
  }
}

async function confirm() {
  const { id, slug } = props.template
  if (pending.has(id)) {
    return
  }
  pending.add(id)
  const requestedAt = performance.now()
  try {
    await TemplateService($client).delete(slug)
    deleted(id, false, requestedAt)
  } catch (error) {
    // The template wasn't found, so it's already deleted, for example in another
    // tab.
    if (error.response?.status === 404) {
      deleted(id, true, requestedAt)
    } else {
      notifyIf(error, 'templates')
    }
  } finally {
    pending.delete(id)
  }
}

defineExpose({ show, hide })
</script>
