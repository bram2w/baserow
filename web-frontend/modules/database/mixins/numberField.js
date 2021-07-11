import { NumberFieldType } from '@baserow/modules/database/fieldTypes'

/**
 * This mixin contains some method overrides for validating and formatting the
 * number field. This mixin is used in both the GridViewFieldNumber and
 * RowEditFieldNumber components.
 */
export default {
  methods: {
    beforeSave(value) {
      return NumberFieldType.formatNumber(this.field, value)
    },
  },
}
