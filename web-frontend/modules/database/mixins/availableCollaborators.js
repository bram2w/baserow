export default {
  computed: {
    groupCollaborators() {
      const groupId = this.$store.getters['group/selectedId']
      const group = this.$store.getters['group/get'](groupId)
      return group.users
    },
    availableCollaborators() {
      // When converting from a CollaboratorField to another field it can happen
      // that this property is being computed with the value (this.value) of the
      // converted to field type. It can either be null, or not an array. In both cases
      // we can safely return an empty array.
      if (!Array.isArray(this.value)) {
        return []
      }
      const ids = this.value.map((item) => item.id)
      const result = this.groupCollaborators.filter(
        (item) => !ids.includes(item.user_id)
      )
      return result
    },
  },
}
