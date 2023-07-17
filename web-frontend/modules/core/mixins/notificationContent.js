import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  methods: {
    markAsReadAndHandleClick(evt) {
      this.$emit('click')

      this.markAsRead()

      if (typeof this.handleClick === 'function') {
        this.handleClick(evt)
      }
    },
    async markAsRead() {
      const notification = this.notification
      if (notification.read) {
        return
      }

      try {
        await this.$store.dispatch('notification/markAsRead', { notification })
      } catch (err) {
        notifyIf(err, 'error')
      }
    },
  },
}
