<template>
  <div
    v-if="elementMode === 'editing' || isVisible"
    class="element__wrapper"
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
    <div class="element__inner-wrapper" :style="innerWrapperStyles">
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
import _ from 'lodash'
import { resolveColor } from '@baserow/modules/core/utils/colors'
import { themeToColorVariables } from '@baserow/modules/builder/utils/theme'

import { BACKGROUND_TYPES, WIDTH_TYPES } from '@baserow/modules/builder/enums'

export default {
  name: 'PageElement',
  inject: ['builder', 'page', 'mode'],
  provide() {
    return {
      mode: this.elementMode,
    }
  },
  props: {
    element: {
      type: Object,
      required: true,
    },
    forceMode: {
      type: String,
      required: false,
      default: null,
    },
  },
  computed: {
    BACKGROUND_TYPES: () => BACKGROUND_TYPES,
    WIDTH_TYPES: () => WIDTH_TYPES,
    colorVariables() {
      return themeToColorVariables(this.builder.theme)
    },
    elementMode() {
      return this.forceMode !== null ? this.forceMode : this.mode
    },
    component() {
      const elementType = this.$registry.get('element', this.element.type)
      const componentName =
        this.elementMode === 'editing' ? 'editComponent' : 'component'
      return elementType[componentName]
    },
    children() {
      return this.$store.getters['element/getChildren'](this.page, this.element)
    },
    isVisible() {
      switch (this.element.visibility) {
        case 'logged-in':
          return this.$store.getters['userSourceUser/isAuthenticated']
        case 'not-logged':
          return !this.$store.getters['userSourceUser/isAuthenticated']
        default:
          return true
      }
    },
    allowedStyles() {
      const parentElement = this.$store.getters['element/getElementById'](
        this.page,
        this.element.parent_element_id
      )

      const elementType = this.$registry.get('element', this.element.type)
      const parentElementType = this.parentElement
        ? this.$registry.get('element', parentElement?.type)
        : null

      return !parentElementType
        ? elementType.styles
        : _.difference(
            elementType.styles,
            parentElementType.childStylesForbidden
          )
    },

    /**
     * Computes an object containing all the style properties that must be set on
     * the element wrapper.
     */
    wrapperStyles() {
      const styles = {
        style_background_color: {
          '--background-color':
            this.element.style_background === BACKGROUND_TYPES.COLOR.value
              ? this.resolveColor(
                  this.element.style_background_color,
                  this.colorVariables
                )
              : 'transparent',
        },
        style_border_top: {
          '--border-top': this.border(
            this.element.style_border_top_size,
            this.element.style_border_top_color
          ),
        },
        style_border_bottom: {
          '--border-bottom': this.border(
            this.element.style_border_bottom_size,
            this.element.style_border_bottom_color
          ),
        },
        style_border_left: {
          '--border-left': this.border(
            this.element.style_border_left_size,
            this.element.style_border_left_color
          ),
        },
        style_border_right: {
          '--border-right': this.border(
            this.element.style_border_right_size,
            this.element.style_border_right_color
          ),
        },
      }

      return Object.keys(styles).reduce((acc, key) => {
        if (this.allowedStyles.includes(key)) {
          acc = { ...acc, ...styles[key] }
        }
        return acc
      }, {})
    },

    /**
     * Computes an object containing all the style properties that must be set on
     * the element inner wrapper.
     */
    innerWrapperStyles() {
      const styles = {
        style_padding_top: {
          '--padding-top': `${this.element.style_padding_top || 0}px`,
        },
        style_padding_bottom: {
          '--padding-bottom': `${this.element.style_padding_bottom || 0}px`,
        },
        style_padding_left: {
          '--padding-left': `${this.element.style_padding_left || 0}px`,
        },
        style_padding_right: {
          '--padding-right': `${this.element.style_padding_right || 0}px`,
        },
      }

      return Object.keys(styles).reduce((acc, key) => {
        if (this.allowedStyles.includes(key)) {
          acc = { ...acc, ...styles[key] }
        }
        return acc
      }, {})
    },
  },
  methods: {
    resolveColor,
    border(size, color) {
      return `solid ${size || 0}px ${this.resolveColor(
        color,
        this.colorVariables
      )}`
    },
  },
}
</script>
