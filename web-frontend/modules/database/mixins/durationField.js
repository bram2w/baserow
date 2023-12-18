import { DurationFieldType } from '@baserow/modules/database/fieldTypes'

/**
 * This mixin contains some method overrides for validating and formatting the
 * duration field. This mixin is used in both the GridViewFieldDuration and
 * RowEditFieldDuration components.
 */
export default {
  data() {
    return {
      errorMsg: null,
      formattedValue: this.formatValue(this.field, this.value),
    }
  },
  methods: {
    isValid() {
      return this.errorMsg === null
    },
    getError() {
      return this.errorMsg
    },
    formatValue(field, value) {
      return DurationFieldType.formatValue(field, value)
    },
    updateFormattedValue(field, value) {
      this.formattedValue = this.formatValue(field, value)
    },
    updateCopy(field, value) {
      this.errorMsg = this.getValidationError(value)
      if (this.errorMsg !== null) {
        return
      }
      const newCopy = DurationFieldType.parseInputValue(field, value)
      if (newCopy !== this.copy) {
        this.copy = newCopy
      }
    },
    onKeyPress(field, event) {
      if (!/\d/.test(event.key) && event.key !== '.' && event.key !== ':') {
        return event.preventDefault()
      }
    },
  },
}
