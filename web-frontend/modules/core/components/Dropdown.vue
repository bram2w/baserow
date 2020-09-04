<template>
  <div class="dropdown">
    <a class="dropdown__selected" @click="show()">
      <template v-if="hasValue()">
        <i
          v-if="selectedIcon"
          class="dropdown__selected-icon fas"
          :class="'fa-' + selectedIcon"
        ></i>
        {{ selectedName }}
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
          :placeholder="searchText"
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
      required: false,
      default: null,
    },
    searchText: {
      type: String,
      required: false,
      default: 'Search',
    },
  },
  computed: {
    selectedName() {
      return this.getSelectedProperty(this.value, 'name')
    },
    selectedIcon() {
      return this.getSelectedProperty(this.value, 'icon')
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
     * Loops over all children to see if any of the values match with given value. If
     * so the requested property of the child is returned
     */
    getSelectedProperty(value, property) {
      for (const i in this.$children) {
        const item = this.$children[i]
        if (item.value === value) {
          return item[property]
        }
      }
      return ''
    },
  },
}
</script>
