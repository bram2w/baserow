<template>
  <div ref="cell" class="grid-view__cell active">
    <div
      ref="dropdownLink"
      class="grid-field-single-select grid-field-single-select--selected"
      :class="{ 'grid-field-single-select--read-only': readOnly }"
      @click="toggleDropdown()"
    >
      <div
        v-if="value !== null"
        class="grid-field-single-select__option"
        :class="'background-color--' + value.color"
      >
        {{ value.value }}
      </div>
      <i
        v-if="!readOnly"
        class="fa fa-caret-down grid-field-single-select__icon"
      ></i>
    </div>
    <FieldSingleSelectDropdown
      v-if="!readOnly"
      ref="dropdown"
      :value="valueId"
      :options="field.select_options"
      :show-input="false"
      :allow-create-option="true"
      class="dropdown--floating grid-field-single-select__dropdown"
      @show="editing = true"
      @hide="editing = false"
      @input="updateValue($event, value)"
      @create-option="createOption($event)"
    ></FieldSingleSelectDropdown>
  </div>
</template>

<script>
import gridField from '@baserow/modules/database/mixins/gridField'
import { isPrintableUnicodeCharacterKeyPress } from '@baserow/modules/core/utils/events'
import singleSelectField from '@baserow/modules/database/mixins/singleSelectField'

export default {
  mixins: [gridField, singleSelectField],
  data() {
    return {
      editing: false,
    }
  },
  methods: {
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
</script>
