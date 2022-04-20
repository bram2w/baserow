import { mapGetters } from 'vuex'

import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  computed: {
    ...mapGetters({
      undoLoading: 'undoRedo/isUndoing',
      redoLoading: 'undoRedo/isRedoing',
    }),
  },
  methods: {
    async undo(showLoadingNotification = true) {
      await this.action('undo', showLoadingNotification)
    },
    async redo(showLoadingNotification = true) {
      await this.action('redo', showLoadingNotification)
    },
    async action(name, showLoadingNotification = true) {
      try {
        await this.$store.dispatch(`undoRedo/${name}`, {
          showLoadingNotification,
        })
      } catch (e) {
        notifyIf(e)
      }
    },
  },
}
