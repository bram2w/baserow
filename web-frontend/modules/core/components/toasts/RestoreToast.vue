<template>
  <button
    class="button toast__undo-delete"
    :disabled="loading"
    :class="{
      'button--loading': loading,
      'toast__undo-delete--pulsing': pulsing,
    }"
    @click="restore"
  >
    <i class="button__icon fas fa-undo"></i>
    {{
      $t('restoreToast.restore', {
        type: $t('trashType.' + toast.data.trash_item_type),
      })
    }}
  </button>
</template>

<script>
import TrashService from '@baserow/modules/core/services/trash'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'RestoreToast',
  props: {
    toast: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      pulsing: true,
    }
  },
  mounted() {
    setTimeout(() => {
      this.pulsing = false
    }, 2000)
    setTimeout(() => {
      this.close()
    }, 5000)
  },
  methods: {
    close() {
      this.$store.dispatch('toast/remove', this.toast)
    },
    async restore() {
      this.loading = true
      this.pulsing = false
      try {
        await TrashService(this.$client).restore(this.toast.data)
      } catch (error) {
        notifyIf(error, 'trash')
      }
      this.close()
      this.loading = false
    },
  },
}
</script>
