<template>
  <div class="card-rich-text">
    <RichTextEditor
      :content-scaled="true"
      :editable="false"
      :enable-rich-text-formatting="true"
      :value="value"
    ></RichTextEditor>
  </div>
</template>

<script>
import RichTextEditor from '@baserow/modules/core/components/editor/RichTextEditor.vue'

export default {
  components: { RichTextEditor },
  props: {
    value: {
      type: String,
      default: '',
    },
  },
  height: 32,
  computed: {
    richValue() {
      return this.value || ''
    },
  },
}
</script>
