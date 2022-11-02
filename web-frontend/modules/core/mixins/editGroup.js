import { notifyIf } from '@baserow/modules/core/utils/error'

/**
 * Some helper method to modify groups used by the sidebar and dashboard.
 */
export default {
  methods: {
    setLoading(group, value) {
      this.$store.dispatch('group/setItemLoading', { group, value })
    },
    enableRename() {
      this.$refs.context.hide()
      this.$refs.rename.edit()
    },
    async renameGroup(group, event) {
      this.setLoading(group, true)

      try {
        await this.$store.dispatch('group/update', {
          group,
          values: {
            name: event.value,
          },
        })
      } catch (error) {
        this.$refs.rename.set(event.oldValue)
        notifyIf(error, 'group')
      }

      this.setLoading(group, false)
    },
    async selectGroup(group) {
      await this.$store.dispatch('group/select', group)
      this.$emit('selected')
    },
  },
}
