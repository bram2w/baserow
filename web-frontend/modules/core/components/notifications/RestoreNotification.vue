<template>
  <button
    class="button undo-delete-notification"
    :disabled="loading"
    :class="{
      'button--loading': loading,
      'undo-delete-notification--pulsing': pulsing,
    }"
    @click="restore"
  >
    <i class="button__icon fas fa-undo"></i>
    {{
      $t('restoreNotification.restore', {
        type: $t('trashType.' + notification.data.trash_item_type),
      })
    }}
  </button>
</template>

<script>
import TrashService from '@baserow/modules/core/services/trash'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'RestoreNotification',
  props: {
    notification: {
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
      this.$store.dispatch('notification/remove', this.notification)
    },
    async restore() {
      this.loading = true
      this.pulsing = false
      try {
        await TrashService(this.$client).restore(this.notification.data)
      } catch (error) {
        notifyIf(error, 'trash')
      }
      this.close()
      this.loading = false
    },
  },
}
</script>
