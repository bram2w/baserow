<template>
  <div
    class="page-root-element__inner"
    :style="{
      '--background-color':
        element.style_background === BACKGROUND_TYPES.COLOR.value
          ? resolveColor(element.style_background_color, colorVariables)
          : 'transparent',
      '--border-top': border(
        element.style_border_top_size,
        element.style_border_top_color
      ),
      '--border-bottom': border(
        element.style_border_bottom_size,
        element.style_border_bottom_color
      ),
    }"
  >
    <div
      class="element__wrapper element__wrapper--normal-width"
      :class="{
        'element__wrapper--full-width':
          element.style_width === WIDTH_TYPES.FULL.value,
        'element__wrapper--medium-width':
          element.style_width === WIDTH_TYPES.MEDIUM.value,
        'element__wrapper--small-width':
          element.style_width === WIDTH_TYPES.SMALL.value,
      }"
      :style="wrapperStyles"
    >
      <component
        :is="component"
        :element="element"
        :children="children"
        class="element"
      />
    </div>
  </div>
</template>

<script>
import pageElement from '@baserow/modules/builder/mixins/pageElement'
import { BACKGROUND_TYPES, WIDTH_TYPES } from '@baserow/modules/builder/enums'

export default {
  name: 'PageRootElement',
  mixins: [pageElement],
  computed: {
    BACKGROUND_TYPES: () => BACKGROUND_TYPES,
    WIDTH_TYPES: () => WIDTH_TYPES,
  },
  methods: {
    border(size, color) {
      return `solid ${size || 0}px ${this.resolveColor(
        color,
        this.colorVariables
      )}`
    },
  },
}
</script>
