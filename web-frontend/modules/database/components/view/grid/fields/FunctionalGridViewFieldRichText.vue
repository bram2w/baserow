<template>
  <div class="grid-view__cell grid-field-long-text__cell">
    <div class="grid-field-long-text">
      <RichTextEditor
        :content-scaled="true"
        :editable="false"
        :enable-rich-text-formatting="true"
        :value="valuePreview"
      ></RichTextEditor>
    </div>
  </div>
</template>

<script>
import RichTextEditor from '@baserow/modules/core/components/editor/RichTextEditor.vue'

export default {
  components: { RichTextEditor },
  props: {
    value: {
      type: String,
      required: false,
      default: null,
    },
  },
  computed: {
    valuePreview() {
      const previewMaxLength = 100
      if (this.value?.length > previewMaxLength) {
        return this.value?.substring(0, previewMaxLength) + '...'
      } else {
        return this.value || ''
      }
    },
  },
}
</script>
