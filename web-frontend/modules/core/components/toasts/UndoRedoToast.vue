<template>
  <Toast :icon="stateContent.icon" :loading="stateContent.loading">
    <template #title>{{ stateContent.title }} </template>
    <span>{{ stateContent.content }} </span>
  </Toast>
</template>

<script>
import Toast from '@baserow/modules/core/components/toasts/Toast'
import { UNDO_REDO_STATES } from '@baserow/modules/core/utils/undoRedoConstants'

export default {
  name: 'UndoRedoToast',
  components: {
    Toast,
  },
  props: {
    state: {
      type: String,
      required: true,
    },
  },
  computed: {
    stateContent() {
      function base({ loading = false, icon = '', title = '', content = '' }) {
        return { loading, icon, title, content }
      }

      switch (this.state) {
        case UNDO_REDO_STATES.UNDONE:
          return base({
            icon: 'iconoir-check',
            title: this.$t('undoRedoToast.undoneTitle'),
            content: this.$t('undoRedoToast.undoneText'),
          })
        case UNDO_REDO_STATES.REDONE:
          return base({
            icon: 'iconoir-check',
            title: this.$t('undoRedoToast.redoneTitle'),
            content: this.$t('undoRedoToast.redoneText'),
          })
        case UNDO_REDO_STATES.UNDOING:
          return base({
            loading: true,
            title: this.$t('undoRedoToast.undoingTitle'),
            content: this.$t('undoRedoToast.undoingText'),
          })
        case UNDO_REDO_STATES.REDOING:
          return base({
            loading: true,
            title: this.$t('undoRedoToast.redoingTitle'),
            content: this.$t('undoRedoToast.redoingText'),
          })
        case UNDO_REDO_STATES.NO_MORE_UNDO:
          return base({
            icon: 'iconoir-cancel',
            title: this.$t('undoRedoToast.failed'),
            content: this.$t('undoRedoToast.noMoreUndo'),
          })
        case UNDO_REDO_STATES.NO_MORE_REDO:
          return base({
            icon: 'iconoir-cancel',
            title: this.$t('undoRedoToast.failed'),
            content: this.$t('undoRedoToast.noMoreRedo'),
          })
        case UNDO_REDO_STATES.ERROR_WITH_UNDO:
          return base({
            icon: 'iconoir-exclamation',
            title: this.$t('undoRedoToast.failed'),
            content: this.$t('undoRedoToast.skippingUndoDueToError'),
          })
        case UNDO_REDO_STATES.ERROR_WITH_REDO:
          return base({
            icon: 'iconoir-exclamation',
            title: this.$t('undoRedoToast.failed'),
            content: this.$t('undoRedoToast.skippingRedoDueToError'),
          })
        default:
          return base()
      }
    },
  },
}
</script>
