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
    async undo(showLoadingToast = true) {
      await this.action('undo', showLoadingToast)
    },
    async redo(showLoadingToast = true) {
      await this.action('redo', showLoadingToast)
    },
    async action(name, showLoadingToast = true) {
      try {
        await this.$store.dispatch(`undoRedo/${name}`, {
          showLoadingToast,
        })
      } catch (e) {
        notifyIf(e)
      }
    },
  },
}
