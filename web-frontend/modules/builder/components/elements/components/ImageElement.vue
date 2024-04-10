<template>
  <div :class="classes" class="image_element">
    <div
      class="image_element__img_wrapper"
      :class="imageConstraintClass"
      :style="{
        '--max-width': styleMaxWidth,
        '--max-height': styleMaxHeight,
      }"
    >
      <img
        class="image_element__img"
        :alt="resolvedAltText || $t('imageElement.emptyState')"
        :src="imageSource"
      />
    </div>
  </div>
</template>

<script>
import element from '@baserow/modules/builder/mixins/element'
import { IMAGE_SOURCE_TYPES } from '@baserow/modules/builder/enums'
import { ensureString } from '@baserow/modules/core/utils/validator'

export default {
  name: 'ImageElement',
  mixins: [element],
  props: {
    /**
     * @type {Object}
     * @property {string} image_source_type - If the image is uploaded or has a url
     * @property {Object} image_file - The image file uploaded (optional)
     * @property {string} image_url - The url of the image source (optional)
     * @property {string} alt_text - The text that's displayed when the image can't load
     * @property {string} alignment - The alignment of the element on the page
     * @property {string} style_max_width - The max-width to apply to the element.
     * @property {string} style_max_height - The max-height to apply to the element.
     * @property {string} style_image_constraint - The image constraint type to use.
     */
    element: {
      type: Object,
      required: true,
    },
  },
  computed: {
    styleMaxWidth() {
      return this.element.style_max_width
        ? `${this.element.style_max_width}%`
        : '100%'
    },
    styleMaxHeight() {
      return this.element.style_max_height
        ? `${this.element.style_max_height}px`
        : ''
    },
    imageConstraintClass() {
      return {
        'image_element__img_wrapper--cover':
          this.element.style_image_constraint === 'cover',
        'image_element__img_wrapper--contain':
          this.element.style_image_constraint === 'contain',
        'image_element__img_wrapper--full-width':
          this.element.style_image_constraint === 'full-width',
        'image_element__img_wrapper--max-height': this.element.styleMaxHeight,
      }
    },
    imageSource() {
      return this.element.image_source_type === IMAGE_SOURCE_TYPES.UPLOAD
        ? this.element.image_file?.url
        : this.resolvedURL
    },
    resolvedAltText() {
      return ensureString(this.resolveFormula(this.element.alt_text))
    },
    resolvedURL() {
      return ensureString(this.resolveFormula(this.element.image_url))
    },
    classes() {
      return {
        [`element--alignment-horizontal-${this.element.alignment}`]: true,
        'element--no-value': !this.imageSource && !this.element.alt_text,
      }
    },
  },
}
</script>
