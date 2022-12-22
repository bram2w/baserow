export default {
  methods: {
    canBeEdited(authProviderType) {
      return (
        this.$registry
          .get('authProvider', authProviderType)
          .getAdminSettingsFormComponent() != null
      )
    },
    canBeDeleted(authProviderType) {
      const getType = this.$store.getters['authProviderAdmin/getType']
      const providerTypeData = getType(authProviderType)
      return providerTypeData.canDeleteExistingProviders
    },
    hasContextMenu(authProviderType) {
      return (
        this.canBeEdited(authProviderType) ||
        this.canBeDeleted(authProviderType)
      )
    },
  },
}
