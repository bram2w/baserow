export default {
  computed: {
    availableSelectOptions() {
      const ids = this.value.map((item) => item.id)
      return this.field.select_options.filter((item) => !ids.includes(item.id))
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
     * Checks if the new value is a valid select_option id for the field and if
     * so will add it to a new values list. If this new list of values is unequal
     * to the old list of values an update event will be emitted which will result
     * in an API call in order to persist the new value to the field.
     */
    updateValue(newId, oldValue) {
      if (!oldValue) {
        oldValue = []
      }
      const newOption =
        this.field.select_options.find((option) => option.id === newId) || null

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
