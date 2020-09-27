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
      <div v-if="showSearch" class="select__search">
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
      <ul ref="items" class="select__items">
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
    showSearch: {
      type: Boolean,
      required: false,
      default: true,
    },
  },
  data() {
    return {
      loaded: false,
      open: false,
      name: null,
      icon: null,
      query: '',
    }
  },
  computed: {
    selectedName() {
      return this.getSelectedProperty(this.value, 'name')
    },
    selectedIcon() {
      return this.getSelectedProperty(this.value, 'icon')
    },
  },
  watch: {
    value() {
      this.$nextTick(() => {
        // When the value changes we want to forcefully reload the selectName and
        // selectedIcon a little bit later because the children might have changed.
        this.forceRefreshSelectedValue()
      })
    },
  },
  mounted() {
    // When the component is mounted we want to forcefully reload the selectedName and
    // selectedIcon.
    this.forceRefreshSelectedValue()
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

      this.$nextTick(() => {
        // We have to wait for the input to be visible before we can focus.
        this.showSearch && this.$refs.search.focus()

        // Scroll to the selected child.
        this.$children.forEach((child) => {
          if (child.value === this.value) {
            this.$refs.items.scrollTop =
              child.$el.offsetTop -
              child.$el.clientHeight -
              Math.round(this.$refs.items.clientHeight / 2)
          }
        })
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
    /**
     * A nasty hack, but in some cases the $children have not yet been loaded when the
     * `selectName` and `selectIcon` are computed. This would result in an empty
     * initial value of the Dropdown because the correct value can't be extracted from
     * the DropdownItem. With this hack we force the computed properties to recompute
     * when the component is mounted. At this moment the $children have been added.
     */
    forceRefreshSelectedValue() {
      this._computedWatchers.selectedName.run()
      this._computedWatchers.selectedIcon.run()
      this.$forceUpdate()
    },
  },
}
</script>
