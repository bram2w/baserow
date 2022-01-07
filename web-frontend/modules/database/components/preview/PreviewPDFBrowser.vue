<template>
  <div class="preview__iframe-wrapper">
    <iframe class="preview__iframe" :src="url" />
  </div>
</template>

<script>
export default {
  name: 'PreviewPDFBrowser',
  props: {
    url: {
      type: String,
      required: true,
    },
  },
}
</script>
