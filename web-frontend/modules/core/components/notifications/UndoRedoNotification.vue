<template>
  <div class="alert alert--simple alert--with-shadow alert--has-icon">
    <div class="alert__icon">
      <div
        v-if="stateContent.loading"
        class="loading alert__icon-loading"
      ></div>
      <i
        v-if="!stateContent.loading"
        class="fas"
        :class="stateContent.icon"
      ></i>
    </div>
    <div class="alert__title">{{ stateContent.title }}</div>
    <p class="alert__content">{{ stateContent.content }}</p>
  </div>
</template>

<script>
import { UNDO_REDO_STATES } from '@baserow/modules/core/utils/undoRedoConstants'

export default {
  name: 'UndoRedoNotification',
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
            icon: 'fa-check',
            title: this.$t('undoRedoNotification.undoneTitle'),
            content: this.$t('undoRedoNotification.undoneText'),
          })
        case UNDO_REDO_STATES.REDONE:
          return base({
            icon: 'fa-check',
            title: this.$t('undoRedoNotification.redoneTitle'),
            content: this.$t('undoRedoNotification.redoneText'),
          })
        case UNDO_REDO_STATES.UNDOING:
          return base({
            loading: true,
            title: this.$t('undoRedoNotification.undoingTitle'),
            content: this.$t('undoRedoNotification.undoingText'),
          })
        case UNDO_REDO_STATES.REDOING:
          return base({
            loading: true,
            title: this.$t('undoRedoNotification.redoingTitle'),
            content: this.$t('undoRedoNotification.redoingText'),
          })
        case UNDO_REDO_STATES.NO_MORE_UNDO:
          return base({
            icon: 'fa-times',
            title: this.$t('undoRedoNotification.failed'),
            content: this.$t('undoRedoNotification.noMoreUndo'),
          })
        case UNDO_REDO_STATES.NO_MORE_REDO:
          return base({
            icon: 'fa-times',
            title: this.$t('undoRedoNotification.failed'),
            content: this.$t('undoRedoNotification.noMoreRedo'),
          })
        case UNDO_REDO_STATES.ERROR_WITH_UNDO:
          return base({
            icon: 'fa-exclamation',
            title: this.$t('undoRedoNotification.failed'),
            content: this.$t('undoRedoNotification.skippingUndoDueToError'),
          })
        case UNDO_REDO_STATES.ERROR_WITH_REDO:
          return base({
            icon: 'fa-exclamation',
            title: this.$t('undoRedoNotification.failed'),
            content: this.$t('undoRedoNotification.skippingRedoDueToError'),
          })
        default:
          return base()
      }
    },
  },
}
</script>
