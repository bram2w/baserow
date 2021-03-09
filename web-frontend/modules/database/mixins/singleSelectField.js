import { notifyIf } from '@baserow/modules/core/utils/error'
import { clone } from '@baserow/modules/core/utils/object'
import { colors } from '@baserow/modules/core/utils/colors'
import FieldSingleSelectDropdown from '@baserow/modules/database/components/field/FieldSingleSelectDropdown'

export default {
  components: { FieldSingleSelectDropdown },
  computed: {
    valueId() {
      return this.value && this.value !== null ? this.value.id : null
    },
  },
  methods: {
    /**
     * Checks if the new value has changed and if so it will be updated.
     */
    updateValue(newId, oldValue) {
      const newValue =
        this.field.select_options.find((option) => option.id === newId) || null
      const oldId = oldValue !== null ? oldValue.id : null

      if (newId !== oldId) {
        this.$emit('update', newValue, oldValue)
      }
    },
    /**
     * Adds a new select option to the field and then updates the field. This method is
     * called from the dropdown, the user can create a new optionfrom  there if no
     * options are found matching his search query.
     */
    async createOption({ value, done }) {
      const values = { select_options: clone(this.field.select_options) }
      values.select_options.push({
        value,
        color: colors[Math.floor(Math.random() * colors.length)],
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
