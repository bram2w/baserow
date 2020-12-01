<template>
  <div class="file-field-modal__preview-image-wrapper">
    <div v-if="!loaded" class="file-field-modal__preview-image-loading"></div>
    <img
      :src="src"
      class="file-field-modal__preview-image"
      :class="{ 'file-field-modal__preview-image--hidden': !loaded }"
      @load="loaded = true"
    />
  </div>
</template>

<script>
export default {
  name: 'FileFieldModalImage',
  props: {
    src: {
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
