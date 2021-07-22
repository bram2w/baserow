import { isDomElement, isElement } from '@baserow/modules/core/utils/dom'

export default {
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
    showInput: {
      type: Boolean,
      required: false,
      default: true,
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      loaded: false,
      open: false,
      name: null,
      icon: null,
      query: '',
      hasItems: true,
      hover: null,
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
     * Toggles the open state of the dropdown menu.
     */
    toggle(target, value) {
      if (value === undefined) {
        value = !this.open
      }

      if (value) {
        this.show(target)
      } else {
        this.hide()
      }
    },
    /**
     * Shows the lists of choices, so a user can change the value.
     */
    show(target) {
      if (this.disabled) {
        return
      }

      const isElementOrigin = isDomElement(target)

      this.open = true
      this.hover = this.value
      this.opener = isElementOrigin ? target : null
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
          !isElement(this.$el, event.target) &&
          // If the click was not on the opener because he can trigger the toggle
          // method.
          !isElement(this.opener, event.target)
        ) {
          this.hide()
        }
      }
      document.body.addEventListener('click', this.$el.clickOutsideEvent)

      this.$el.keydownEvent = (event) => {
        if (
          // Check if the context menu is still open
          this.open &&
          // Check if the user has hit either of the keys we care about. If not,
          // ignore.
          (event.code === 'ArrowUp' || event.code === 'ArrowDown')
        ) {
          // Prevent scrolling up and down while pressing the up and down key.
          event.stopPropagation()
          event.preventDefault()
          this.handleUpAndDownArrowPress(event)
        }
        // Allow the Enter key to select the value that is currently being hovered
        // over.
        if (this.open && event.code === 'Enter') {
          // Prevent submitting the whole form when pressing the enter key while the
          // dropdown is open.
          event.preventDefault()
          this.select(this.hover)
        }
      }
      document.body.addEventListener('keydown', this.$el.keydownEvent)
    },
    /**
     * Hides the list of choices. If something change in this method, you might need
     * to update the hide method of the `PaginatedDropdown` component because it
     * contains a partial copy of this code.
     */
    hide() {
      this.open = false
      this.$emit('hide')

      // Make sure that all the items are visible the next time we open the dropdown.
      this.query = ''
      this.search(this.query)

      document.body.removeEventListener('click', this.$el.clickOutsideEvent)
      document.body.removeEventListener('keydown', this.$el.keydownEvent)
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
      this.hasItems = query === ''
      this.$children.forEach((item) => {
        if (item.search(query)) {
          this.hasItems = true
        }
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
     * Returns true if there is a value.
     * @return {boolean}
     */
    hasValue() {
      for (const i in this.$children) {
        const item = this.$children[i]
        if (item.value === this.value) {
          return true
        }
      }
      return false
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
    /**
     * Method that is called when the arrow up or arrow down key is pressed. Based on
     * the index of the current child, the next child enabled child is set as hover.
     */
    handleUpAndDownArrowPress(event) {
      const children = this.$children.filter(
        (child) => !child.disabled && child.isVisible(this.query)
      )

      const isArrowUp = event.code === 'ArrowUp'
      let index = children.findIndex((item) => item.value === this.hover)
      index = isArrowUp ? index - 1 : index + 1

      // Check if the new index is within the allowed range.
      if (index < 0 || index > children.length - 1) {
        return
      }

      const next = children[index]
      this.hover = next.value
      this.$refs.items.scrollTop = this.getScrollTopAmountForNextChild(
        next,
        isArrowUp
      )
    },
    /**
     * This method calculates the expected container scroll top offset if the next
     * child is selected. This is for example used when navigating with the arrow keys.
     * If the element to scroll to is below the current dropdown's bottom scroll
     * position, then scroll so that the item to scroll to is the last visible item
     * in the dropdown window. Conversely if the element to scroll to is above the
     * current dropdown's top scroll position then scroll so that the item to scroll
     * to is the first viewable item in the dropdown window.
     */
    getScrollTopAmountForNextChild(itemToScrollTo, isArrowUp) {
      // Styles of the itemToScroll to. Needed in order to get margins and height
      const itemToScrollToStyles =
        itemToScrollTo.$el.currentStyle ||
        window.getComputedStyle(itemToScrollTo.$el)

      // Styles of the ref items (the dropdown window). Needed in order to get
      // ::before height and ::after height
      const dropdownWindowBeforeStyles =
        this.$refs.items.currentStyle ||
        window.getComputedStyle(this.$refs.items, ':before')

      const dropdownWindowAfterStyles =
        this.$refs.items.currentStyle ||
        window.getComputedStyle(this.$refs.items, ':after')

      const dropdownWindowBeforeHeight = parseInt(
        dropdownWindowBeforeStyles.height
      )
      const dropdownWindowAfterHeight = parseInt(
        dropdownWindowAfterStyles.height
      )
      const dropdownWindowHeight = this.$refs.items.clientHeight

      const itemHeight = parseInt(itemToScrollToStyles.height)
      const itemMarginTop = parseInt(itemToScrollToStyles.marginTop)
      const itemMarginBottom = parseInt(itemToScrollToStyles.marginBottom)
      const itemHeightWithMargins =
        itemHeight + itemMarginTop + itemMarginBottom

      // Based on the values set in the SCSS files. The height of a dropdowns select
      // item is set to 32px and the height of the select_items window is set to 4 *
      // 36 (select item height plus margins) plus 20 (heights of before and after
      // pseudo elements) so that there is room for four elements
      const itemsInView =
        (dropdownWindowHeight -
          dropdownWindowBeforeHeight -
          dropdownWindowAfterHeight) /
        itemHeightWithMargins

      // Get the direction of the scrolling.
      const movingDownwards = !isArrowUp
      const movingUpwards = isArrowUp

      // nextItemOutOfView can be used if one wants to check if the item to scroll
      // to is out of view of the current dropdowns bottom scroll position.
      // This happens when the difference between the element to scroll to's
      // offsetTop and the current scrollTop of the dropdown is smaller than height
      // of the dropdown minus the full height of the element
      const nextItemOutOfView =
        itemToScrollTo.$el.offsetTop - this.$refs.items.scrollTop >
        dropdownWindowHeight - itemHeightWithMargins

      // prevItemOutOfView can be used if one wants to check if the item to scroll
      // to is out of view of the current dropdowns top scroll position.
      // This happens when the element to scroll to's offsetTop is smaller than the
      // current scrollTop of the dropdown
      const prevItemOutOfView =
        itemToScrollTo.$el.offsetTop < this.$refs.items.scrollTop

      // When the user is scrolling downwards (i.e. pressing key down)
      // and the itemToScrollTo is out of view we want to add the height of the
      // elements preceding the itemToScrollTo plus the dropdownWindowBeforeHeight.
      // This can be achieved by removing said heights from the itemToScrollTo's
      // offsetTop
      if (nextItemOutOfView && movingDownwards) {
        const elementsHeightBeforeItemToScrollTo =
          itemHeightWithMargins * (itemsInView - 1)

        return (
          itemToScrollTo.$el.offsetTop -
          elementsHeightBeforeItemToScrollTo -
          dropdownWindowBeforeHeight
        )
      }

      // When the user is scrolling upwards (i.e. pressing key up) and the
      // itemToScrollTo is out of view we want to set the scrollPosition to be the
      // offsetTop of the element minus it's top margin and the height of the
      // ::after pseudo element of the ref items element
      if (prevItemOutOfView && movingUpwards) {
        return (
          itemToScrollTo.$el.offsetTop -
          itemMarginTop -
          dropdownWindowAfterHeight
        )
      }

      // In the case that the next item to scroll to is completely visible we simply
      // return the current scroll position so that no scrolling happens
      return this.$refs.items.scrollTop
    },
  },
}
