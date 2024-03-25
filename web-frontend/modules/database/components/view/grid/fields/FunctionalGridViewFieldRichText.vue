<!-- eslint-disable vue/no-v-html -->
<template functional>
  <div
    class="field-rich-text--preview grid-view__cell grid-field-rich-text__cell"
    v-html="$options.methods.renderFormattedValue(props.value)"
  ></div>
</template>

<script>
import { parseMarkdown } from '@baserow/modules/core/editor/markdown'

export default {
  name: 'FunctionalGridViewFieldRichText',
  methods: {
    renderFormattedValue(value) {
      // Take only a part of the text as a preview to avoid rendering a huge amount of
      // HTML that could slow down the page and won't be visible anyway
      let preview = ''
      if (value) {
        preview = value.substring(0, 200)
        if (value.length > 200) {
          preview += '...'
        }
      }
      return parseMarkdown(preview)
    },
  },
}
</script>
