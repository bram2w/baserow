import { notifyIf } from '@baserow/modules/core/utils/error'
import { clone } from '@baserow/modules/core/utils/object'
import { randomColor } from '@baserow/modules/core/utils/colors'

export default {
  methods: {
    /**
     * Adds a new select option to the field and then updates the field. This method is
     * called from the dropdown, the user can create a new option from there if no
     * options are found matching his search query.
     */
    async createOption({ value, done }) {
      const values = { select_options: clone(this.field.select_options) }
      values.select_options.push({
        value,
        color: randomColor(),
      })

      try {
        await this.$store.dispatch('field/update', {
          field: this.field,
          type: this.field.type,
          values,
        })
        done(true)
      } catch (error) {
        notifyIf(error, 'field')
        done(false)
      }
    },
  },
}
