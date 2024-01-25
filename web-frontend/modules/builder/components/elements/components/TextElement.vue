<template>
  <div
    class="text-element"
    :class="{
      'element--no-value': !resolvedValue,
      [`element--alignment-horizontal-${element.alignment}`]: true,
    }"
  >
    <p v-for="paragraph in paragraphs" :key="paragraph.id" class="ab-paragraph">
      {{ paragraph.content }}
    </p>
    <p v-if="!paragraphs.length" class="ab-paragraph">
      {{ $t('textElement.noValue') }}
    </p>
  </div>
</template>

<script>
import element from '@baserow/modules/builder/mixins/element'
import { generateHash } from '@baserow/modules/core/utils/hashing'
import { ensureString } from '@baserow/modules/core/utils/validator'

/**
 * @typedef Text
 * @property {string} content - The text displayed
 * @property {string} id - The id of the paragraph hashed
 */

export default {
  name: 'TextElement',
  mixins: [element],
  props: {
    /**
     * @type {Object}
     * @property {Array.<Text>} value - A list of paragraphs
     * @property {string} alignment - The alignment of the element on the page
     */
    element: {
      type: Object,
      required: true,
    },
  },
  computed: {
    resolvedValue() {
      try {
        return ensureString(this.resolveFormula(this.element.value))
      } catch {
        return ''
      }
    },
    paragraphs() {
      return this.resolvedValue
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
