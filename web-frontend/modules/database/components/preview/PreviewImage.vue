<template>
  <div class="preview__image-wrapper">
    <div v-if="!loaded" class="preview__loading"></div>
    <img
      :src="url"
      class="preview__image"
      :class="{ 'preview--hidden': !loaded }"
      @load="loaded = true"
    />
  </div>
</template>

<script>
export default {
  name: 'PreviewImage',
  props: {
    url: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      loaded: false,
    }
  },
}
</script>
