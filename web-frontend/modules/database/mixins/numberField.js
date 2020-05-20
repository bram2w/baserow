/**
 * This mixin contains some method overrides for validating and formatting the
 * number field. This mixin is used in both the GridViewFieldNumber and
 * RowEditFieldNumber components.
 */
export default {
  methods: {
    /**
     * Generates a human readable error for the user if something is wrong.
     */
    getError() {
      if (this.copy === null || this.copy === '') {
        return null
      }
      if (isNaN(parseFloat(this.copy)) || !isFinite(this.copy)) {
        return 'Invalid number'
      }
      return null
    },
    isValid() {
      return this.getError() === null
    },
    /**
     * Formats the value based on the field's settings. The number will be rounded
     * if to much decimal places are provided and if negative numbers aren't allowed
     * they will be set to 0.
     */
    beforeSave(value) {
      if (
        value === '' ||
        isNaN(value) ||
        value === undefined ||
        value === null
      ) {
        return null
      }
      const decimalPlaces =
        this.field.number_type === 'DECIMAL'
          ? this.field.number_decimal_places
          : 0
      let number = parseFloat(value)
      if (!this.field.number_negative && number < 0) {
        number = 0
      }
      return number.toFixed(decimalPlaces)
    },
  },
}
