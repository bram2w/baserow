<template>
  <div
    class="text-element"
    :class="{
      'element--no-value': !resolvedValue,
    }"
    :style="getStyleOverride('typography')"
  >
    <template v-if="isMarkdown">
      <MarkdownIt
        v-if="element.value"
        :content="
          displayValue ||
          (mode === 'editing' ? $t('textElement.emptyValue') : '&nbsp;')
        "
        :rules="markdownRules"
        @click="onMarkdownClick"
      ></MarkdownIt>
      <ABParagraph v-else>{{ $t('textElement.missingValue') }}</ABParagraph>
    </template>
    <template v-else>
      <ABParagraph v-for="paragraph in paragraphs" :key="paragraph.id">
        {{ paragraph.content }}
      </ABParagraph>
      <ABParagraph v-if="element.value && paragraphs.length === 0">
        {{ mode === 'editing' ? $t('textElement.emptyValue') : '&nbsp;' }}
      </ABParagraph>
      <ABParagraph v-else-if="!element.value">
        {{ $t('textElement.missingValue') }}
      </ABParagraph>
    </template>
  </div>
</template>

<script>
import element from '@baserow/modules/builder/mixins/element'
import { generateHash } from '@baserow/modules/core/utils/hashing'
import { ensureString } from '@baserow/modules/core/utils/validator'
import { TEXT_FORMAT_TYPES } from '@baserow/modules/builder/enums'
import { splitTextMarker } from '@baserow/modules/builder/utils/markdown'
import markdownContent from '@baserow/modules/builder/mixins/markdownContent'

/**
 * @typedef Text
 * @property {string} content - The text displayed
 * @property {string} id - The id of the paragraph hashed
 */

export default {
  name: 'TextElement',
  mixins: [element, markdownContent],
  props: {
    /**
     * @type {Object}
     * @property {Array.<Text>} value - A list of paragraphs
     * @property {string} alignment - The alignment of the element on the page
     * @property {string} format - The format of the text
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
      } catch (e) {
        return ''
      }
    },
    /**
     * The Text element keeps its own `format` setting, but it follows the rule
     * of every other text surface too: a resolved value starting with the
     * Markdown marker renders as Markdown, minus the marker.
     */
    markedValue() {
      return splitTextMarker(this.resolvedValue)
    },
    displayValue() {
      return this.markedValue.text
    },
    isMarkdown() {
      return (
        this.element.format === TEXT_FORMAT_TYPES.MARKDOWN ||
        this.markedValue.format === TEXT_FORMAT_TYPES.MARKDOWN
      )
    },
    paragraphs() {
      return this.displayValue
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
