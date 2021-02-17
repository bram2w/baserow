export default {
  methods: {
    /**
     * Removes an existing relation from the value.
     */
    removeValue(event, value, id) {
      const newValue = JSON.parse(JSON.stringify(value))
      const index = newValue.findIndex((item) => item.id === id)
      if (index === -1) {
        return
      }

      newValue.splice(index, 1)
      this.$emit('update', newValue, value)
    },
    /**
     * Adds a new relation to the value. This typically happens via the modal.
     */
    addValue(value, { row, primary }) {
      // Check if the relation already exists.
      for (let i = 0; i < value.length; i++) {
        if (value[i].id === row.id) {
          return
        }
      }

      // Prepare the new value with all the relations and emit that value to the
      // parent.
      const newValue = JSON.parse(JSON.stringify(value))
      const rowValue = this.$registry
        .get('field', primary.type)
        .toHumanReadableString(primary, row[`field_${primary.id}`])
      newValue.push({
        id: row.id,
        value: rowValue,
      })
      this.$emit('update', newValue, value)
    },
  },
}
