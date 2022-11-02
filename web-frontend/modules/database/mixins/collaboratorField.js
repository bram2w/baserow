import selectDropdown from '@baserow/modules/database/mixins/selectDropdown'

export default {
  mixins: [selectDropdown],
  computed: {
    groupCollaborators() {
      const group = this.$store.getters['group/get'](this.groupId)
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
      return this.groupCollaborators.filter(
        (item) => !ids.includes(item.user_id)
      )
    },
  },
  methods: {
    /**
     * Removes the provided ID from the current values list and emits an update
     * event with the new values list.
     */
    removeValue(event, currentValues, itemIdToRemove) {
      const vals = currentValues.filter((item) => item.id !== itemIdToRemove)
      this.$emit('update', vals, currentValues)
    },
    /**
     * Checks if the new value is valid for the field and if
     * so will add it to a new values list. If this new list of values is unequal
     * to the old list of values an update event will be emitted which will result
     * in an API call in order to persist the new value to the field.
     */
    updateValue(newId, oldValue) {
      if (!oldValue) {
        oldValue = []
      }

      const groupUser =
        this.groupCollaborators.find(
          (groupUser) => groupUser.user_id === newId
        ) || null

      let newOption = null
      if (groupUser) {
        newOption = {
          id: groupUser.user_id,
          name: groupUser.name,
        }
      }

      const newValue = [...oldValue]
      if (newOption) {
        newValue.push(newOption)
      }

      if (JSON.stringify(newValue) !== JSON.stringify(oldValue)) {
        this.$emit('update', newValue, oldValue)
      }
    },
  },
}
