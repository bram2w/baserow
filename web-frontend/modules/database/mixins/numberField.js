import { NumberFieldType } from '@baserow/modules/database/fieldTypes'

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
      if (
        this.copy.split('.')[0].replace('-', '').length >
        NumberFieldType.getMaxNumberLength()
      ) {
        return `Max ${NumberFieldType.getMaxNumberLength()} digits allowed.`
      }
      return null
    },
    isValid() {
      return this.getError() === null
    },
    /**
     * Before the numeric value is saved we might need to do some formatting such that
     * the value is conform the fields requirements.
     */
    beforeSave(value) {
      return NumberFieldType.formatNumber(this.field, value)
    },
  },
}
