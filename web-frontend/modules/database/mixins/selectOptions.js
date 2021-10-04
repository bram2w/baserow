import { notifyIf } from '@baserow/modules/core/utils/error'
import { clone } from '@baserow/modules/core/utils/object'
import { isPrintableUnicodeCharacterKeyPress } from '@baserow/modules/core/utils/events'
import { colors } from '@baserow/modules/core/utils/colors'
import FieldSelectOptionsDropdown from '@baserow/modules/database/components/field/FieldSelectOptionsDropdown'

export default {
  components: { FieldSelectOptionsDropdown },
  methods: {
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
    toggleDropdown(value, query) {
      if (this.readOnly) {
        return
      }

      this.$refs.dropdown.toggle(this.$refs.dropdownLink, value, query)
    },
    hideDropdown() {
      this.$refs.dropdown.hide()
    },
    select() {
      this.$el.keydownEvent = (event) => {
        // If the tab or arrow keys are pressed we don't want to do anything because
        // the GridViewField component will select the next field.
        const ignoredKeys = [9, 37, 38, 39, 40]
        if (ignoredKeys.includes(event.keyCode)) {
          return
        }

        // When the escape key is pressed while editing the value we can hide the
        // dropdown.
        if (event.keyCode === 27 && this.editing) {
          this.hideDropdown()
          return
        }

        // When the enter key, any printable character or F2 is pressed when not editing
        // the value we want to show the dropdown.
        if (
          !this.editing &&
          (event.keyCode === 13 ||
            isPrintableUnicodeCharacterKeyPress(event) ||
            event.key === 'F2')
        ) {
          this.toggleDropdown()
        }
      }
      document.body.addEventListener('keydown', this.$el.keydownEvent)
    },
    beforeUnSelect() {
      document.body.removeEventListener('keydown', this.$el.keydownEvent)
    },
    canSelectNext() {
      return !this.editing
    },
    canCopy() {
      return !this.editing
    },
    canPaste() {
      return !this.editing
    },
    canEmpty() {
      return !this.editing
    },
  },
}
