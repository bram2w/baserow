import { notifyIf } from '@baserow/modules/core/utils/error'
export default {
  methods: {
    setLoading(application, value) {
      this.$store.dispatch('application/setItemLoading', {
        application,
        value,
      })
    },
    getApplicationContextComponent(application) {
      return this.$registry
        .get('application', application.type)
        .getApplicationContextComponent()
    },
    getApplicationTypeName(application) {
      return this.$registry.get('application', application.type).getName()
    },
    handleRenameApplication() {
      this.$refs.rename.edit()
    },
    async renameApplication(application, event) {
      this.setLoading(application, true)

      try {
        await this.$store.dispatch('application/update', {
          application,
          values: {
            name: event.value,
          },
        })
      } catch (error) {
        this.$refs.rename.set(event.oldValue)
        notifyIf(error, 'application')
      }

      this.setLoading(application, false)
    },
  },
}
