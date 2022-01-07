<template>
  <div class="preview__iframe-wrapper">
    <div v-if="!loaded" class="preview__loading"></div>
    <iframe
      class="preview__iframe"
      :class="{ 'preview--hidden': !loaded }"
      :src="`https://docs.google.com/gview?url=${encodedUrl}&embedded=true`"
      @load="loaded = true"
    />
  </div>
</template>

<script>
export default {
  name: 'PreviewOfficeGoogle',
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
  computed: {
    encodedUrl() {
      return encodeURIComponent(this.url)
    },
  },
}
</script>
