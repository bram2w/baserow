<template>
  <div class="preview__video-wrapper">
    <div v-if="!loaded && canRead" class="preview__loading"></div>
    <video
      v-show="canRead"
      ref="videoRef"
      controls
      class="preview__video"
      :class="{ 'preview--hidden': !loaded }"
      @loadstart="loaded = true"
    >
      <source :src="url" :type="mimeType" @error="onError($event)" />
      <slot name="fallback" />
    </video>
    <slot v-if="!canRead" name="fallback" />
  </div>
</template>

<script>
export default {
  name: 'PreviewVideo',
  props: {
    url: {
      type: String,
      required: true,
    },
    mimeType: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      loaded: false,
      canRead: false,
    }
  },
  mounted() {
    if (this.$refs.videoRef.canPlayType(this.mimeType) !== '') {
      // This format should be playable
      this.canRead = true
    }
  },
  methods: {
    onError(e) {
      // Actually this format can't be read, go back to fallback
      this.canRead = false
    },
  },
}
</script>
