export default {
  computed: {
    workspaceCollaborators() {
      const workspace = this.$store.getters['workspace/getSelected']
      return workspace.users.filter((user) => user.to_be_deleted === false)
    },
    availableCollaborators() {
      // When converting from a CollaboratorField to another field it can happen
      // that this property is being computed with the value (this.value) of the
      // converted to field type. It can either be null, or not an array. In both cases
      // we can safely return an empty array.
      if (!Array.isArray(this.value)) {
        return []
      }

      const ids = new Set(this.value.map((item) => item.id))
      const result = this.workspaceCollaborators.filter(
        (item) => !ids.has(item.user_id)
      )
      return result
    },
  },
}
