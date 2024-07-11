<template>
  <div class="ab-image">
    <img class="ab-image__img" :alt="alt" :src="src" />
  </div>
</template>

<script>
/**
 * @typedef ABImage
 */

export default {
  name: 'ABImage',
  props: {
    /**
     * @type {String} - Alternative text to image.
     */
    alt: {
      type: String,
      required: false,
      default: '',
    },
    /**
     * @type {String} - Image url.
     */
    src: {
      type: String,
      required: false,
      default: '',
    },
  },
}
</script>
