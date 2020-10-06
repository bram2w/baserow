import { isValidURL } from '@baserow/modules/core/utils/string'

/**
 * This mixin contains some method overrides for validating and formatting the
 * URL field. This mixin is used in both the GridViewFieldURL and
 * RowEditFieldURL components.
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
      if (!isValidURL(this.copy)) {
        return 'Invalid URL'
      }
      return null
    },
    isValid() {
      return this.getError() === null
    },
  },
}
