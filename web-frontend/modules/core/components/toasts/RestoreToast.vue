<template>
  <Button
    class="toast-button toast-button--bottom"
    :class="{
      'toast-button--pulsing': pulsing,
    }"
    type="primary"
    :disabled="loading"
    :loading="loading"
    @click="restore()"
  >
    <i class="button__icon iconoir-undo"></i>
    {{
      $t('restoreToast.restore', {
        type: $t('trashType.' + toast.data.trash_item_type),
      })
    }}</Button
  >
</template>

<script>
import Button from '@baserow/modules/core/components/Button'
import TrashService from '@baserow/modules/core/services/trash'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'RestoreToast',
  components: {
    Button,
  },
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
