/**
 * This mixin contains some method overrides for validating and formatting the
 * phone number field. This mixin is used in both the GridViewFieldPhoneNumber and
 * RowEditFieldPhoneNumber components.
 */
import { isSimplePhoneNumber } from '@baserow/modules/core/utils/string'

export default {
  methods: {
    /**
     * Generates a human readable error for the user if something is wrong.
     */
    getError() {
      if (this.copy === null || this.copy === '') {
        return null
      }
      if (!isSimplePhoneNumber(this.copy)) {
        return 'Invalid Phone Number'
      }
      return null
    },
    isValid() {
      return this.getError() === null
    },
  },
}
