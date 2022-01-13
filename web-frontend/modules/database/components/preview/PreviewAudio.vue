<template>
  <div class="preview__audio-wrapper">
    <div v-if="!loaded && canRead" class="preview__loading"></div>
    <audio
      v-show="canRead"
      ref="audioRef"
      controls
      class="preview__audio"
      :class="{ 'preview--hidden': !loaded }"
      @loadstart="loaded = true"
    >
      <source :src="url" :type="mimeType" />
      <slot name="fallback" />
    </audio>
    <slot v-if="!canRead" name="fallback" />
  </div>
</template>

<script>
export default {
  name: 'PreviewAudio',
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
    if (this.$refs.audioRef.canPlayType(this.mimeType) !== '') {
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
