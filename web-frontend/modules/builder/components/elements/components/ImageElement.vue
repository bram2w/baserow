<template>
  <div :class="classes" class="image_element">
    <img
      class="image_element__img"
      :alt="element.alt_text || $t('imageElement.emptyState')"
      :src="imageSource"
    />
  </div>
</template>

<script>
import element from '@baserow/modules/builder/mixins/element'
import { IMAGE_SOURCE_TYPES } from '@baserow/modules/builder/enums'

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
     */
    element: {
      type: Object,
      required: true,
    },
  },
  computed: {
    imageSource() {
      return this.element.image_source_type === IMAGE_SOURCE_TYPES.UPLOAD
        ? this.element.image_file?.url
        : this.element.image_url
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
