export default {
  methods: {
    getCollaboratorName(collaboratorValue, store) {
      if (store === undefined) {
        store = this.$store
      }

      // If groups are unavailable, public views are served
      const groups = store.getters['group/getAll']
      if (groups.length === 0) {
        return collaboratorValue.name
      }

      // Otherwise, get name from the store to reflect real-time updates
      const user = store.getters['group/getUserById'](collaboratorValue.id)
      if (user) {
        return user.name
      }

      // Fallback if for some reason the user is missing from the store
      return collaboratorValue.name
    },
    getCollaboratorNameInitials(collaboratorValue, store) {
      return this.getCollaboratorName(collaboratorValue, store)
        .slice(0, 1)
        .toUpperCase()
    },
  },
}
