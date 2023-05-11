<template>
  <div v-if="paragraphs.length">
    <p
      v-for="paragraph in paragraphs"
      :key="paragraph.id"
      class="paragraph-element"
    >
      {{ paragraph.content }}
    </p>
  </div>
  <p v-else class="paragraph-element element--no-value">
    {{ $t('paragraphElement.noValue') }}
  </p>
</template>

<script>
import textElement from '@baserow/modules/builder/mixins/elements/textElement'
import { generateHash } from '@baserow/modules/core/utils/hashing'

export default {
  name: 'ParagraphElement',
  mixins: [textElement],
  props: {
    element: {
      type: Object,
      required: true,
    },
  },
  computed: {
    paragraphs() {
      return this.element.value
        .split('\n')
        .map((line) => line.trim())
        .filter((line) => line)
        .map((line, index) => ({
          content: line,
          id: generateHash(line + index),
        }))
    },
  },
}
</script>
