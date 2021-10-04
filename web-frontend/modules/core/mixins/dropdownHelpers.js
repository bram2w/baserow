export default {
  methods: {
    /**
     * This method is a helper for extracting certain style properties of a parent container
     * and one of it's child items. This is helpful for determining the amount of pixels
     * to scroll in order to get a child element aligned at the bottom of the parent container,
     * either when scrolling by keydown/keyup or manually setting a scroll position.
     *
     * It expects the parent container to have :before and :after pseudo elements.
     *
     * Returns an object containing the following:
     *
     * parentContainerHeight: The height of the parent container.
     * parentContainerAfterHeight: The height of the parents 'after' pseudo element.
     * parentContainerBeforeHeight: The height of the parents 'before' pseudo element.
     * itemHeightWithMargins: The height of the child item including its margins.
     * itemMarginTop: The top margin of the child item.
     * itemMarginBottom: The bottom margin of the child item.
     * itemsInView: The amount of times the child item fits into the parent viewport.
     */
    getStyleProperties(parentContainer, childItem) {
      // Styles of the childItem. Needed in order to get margins and height
      const childItemStyles =
        childItem.currentStyle || window.getComputedStyle(childItem)

      // Styles of the parent container. Needed in order to get
      // ::before height and ::after height
      const parentContainerBeforeStyles =
        parentContainer.currentStyle ||
        window.getComputedStyle(parentContainer, ':before')

      const parentContainerAfterStyles =
        parentContainer.currentStyle ||
        window.getComputedStyle(parentContainer, ':after')

      const parentContainerBeforeHeight = parseInt(
        parentContainerBeforeStyles.height
      )
      const parentContainerAfterHeight = parseInt(
        parentContainerAfterStyles.height
      )
      const parentContainerHeight = parentContainer.clientHeight

      const itemHeight = parseInt(childItemStyles.height)
      const itemMarginTop = parseInt(childItemStyles.marginTop)
      const itemMarginBottom = parseInt(childItemStyles.marginBottom)
      const itemHeightWithMargins =
        itemHeight + itemMarginTop + itemMarginBottom

      // Based on the values set in the SCSS files. The height of a dropdowns select
      // item is set to 32px and the height of the select_items window is set to 4 *
      // 36 (select item height plus margins) plus 20 (heights of before and after
      // pseudo elements) so that there is room for four elements
      const itemsInView =
        (parentContainerHeight -
          parentContainerBeforeHeight -
          parentContainerAfterHeight) /
        itemHeightWithMargins

      return {
        parentContainerHeight,
        parentContainerAfterHeight,
        parentContainerBeforeHeight,
        itemHeightWithMargins,
        itemMarginTop,
        itemMarginBottom,
        itemsInView,
      }
    },
  },
}
