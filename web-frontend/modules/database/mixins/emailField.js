import { isValidEmail } from '@baserow/modules/core/utils/string'

/**
 * This mixin contains some method overrides for validating and formatting the
 * email field. This mixin is used in both the GridViewFieldEmail and
 * RowEditFieldEmail components.
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
      if (this.copy.length > 254) {
        return 'Max 254 chars'
      }
      if (!isValidEmail(this.copy)) {
        return 'Invalid email'
      }
      return null
    },
    isValid() {
      return this.getError() === null
    },
  },
}
