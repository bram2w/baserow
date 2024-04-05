<template>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <div
    class="card-rich-text field-rich-text--preview"
    v-html="formattedValue"
  ></div>
</template>

<script>
import { parseMarkdown } from '@baserow/modules/core/editor/markdown'

export default {
  props: {
    value: {
      type: String,
      default: '',
    },
  },
  height: 32,
  computed: {
    formattedValue() {
      return parseMarkdown(this.value, { openLinkOnClick: true })
    },
  },
}
</script>
