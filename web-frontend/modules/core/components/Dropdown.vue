<template>
  <div class="dropdown">
    <a class="dropdown__selected" @click="show()">
      <template v-if="hasValue()">
        <i
          v-if="icon"
          class="dropdown__selected-icon fas"
          :class="'fa-' + icon"
        ></i>
        {{ name }}
      </template>
      <template v-if="!hasValue()">
        Make a choice
      </template>
      <i class="dropdown__toggle-icon fas fa-caret-down"></i>
    </a>
    <div class="dropdown__items" :class="{ hidden: !open }">
      <div class="select__search">
        <i class="select__search-icon fas fa-search"></i>
        <input
          ref="search"
          v-model="query"
          type="text"
          class="select__search-input"
          placeholder="Search field types"
          @keyup="search(query)"
        />
      </div>
      <ul class="select__items">
        <slot></slot>
      </ul>
    </div>
  </div>
</template>

<script>
import { isElement } from '@baserow/modules/core/utils/dom'

// @TODO focus on tab
export default {
  name: 'Dropdown',
  props: {
    value: {
      type: [String, Number, Boolean, Object],
      required: true,
    },
  },
  data() {
    return {
      open: false,
      name: null,
      icon: null,
      query: '',
    }
  },
  watch: {
    /**
     * If the value changes we have to update the visible name and icon.
     */
    value(newValue) {
      this.setDisplayValue(newValue)
    },
  },
  /**
   * When the dropdown first loads we have to check if there already is a value, if
   * there is, we have to update the displayed name and icon.
   */
  mounted() {
    if (this.hasValue()) {
      this.setDisplayValue(this.value)
    }
  },
  methods: {
    /**
     * Returns true if there is a value.
     * @return {boolean}
     */
    hasValue() {
      return !!this.value
    },
    /**
     * Shows the lists of choices, so a user can change the value.
     */
    show() {
      this.open = true
      this.$emit('show')

      // We have to wait for the input to be visible before we can focus.
      this.$nextTick(() => {
        this.$refs.search.focus()
      })

      // If the user clicks outside the dropdown while the list of choices of open we
      // have to hide them.
      this.$el.clickOutsideEvent = (event) => {
        if (
          // Check if the context menu is still open
          this.open &&
          // If the click was outside the context element because we want to ignore
          // clicks inside it.
          !isElement(this.$el, event.target)
        ) {
          this.hide()
        }
      }
      document.body.addEventListener('click', this.$el.clickOutsideEvent)
    },
    /**
     * Hides the list of choices
     */
    hide() {
      this.open = false
      this.$emit('hide')

      // Make sure that all the items are visible the next time we open the dropdown.
      this.query = ''
      this.search(this.query)

      document.body.removeEventListener('click', this.$el.clickOutsideEvent)
    },
    /**
     * Selects a new value which will also be
     */
    select(value) {
      this.$emit('input', value)
      this.$emit('change', value)
      this.hide()
    },
    /**
     * If not empty it will only show children that contain the given query.
     */
    search(query) {
      this.$children.forEach((item) => {
        item.search(query)
      })
    },
    /**
     * Changes the selected name and icon of the dropdown based on the provided value.
     */
    setDisplayValue(value) {
      this.$children.forEach((item) => {
        if (item.value === value) {
          this.name = item.name
          this.icon = item.icon
        }
      })
    },
  },
}
</script>
