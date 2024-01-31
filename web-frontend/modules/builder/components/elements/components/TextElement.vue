<template>
  <div
    class="text-element"
    :class="{
      'element--no-value': !resolvedValue,
      [`element--alignment-horizontal-${element.alignment}`]: true,
    }"
  >
    <template v-if="element.format === TEXT_FORMAT_TYPES.MARKDOWN">
      <MarkdownIt
        v-if="resolvedValue"
        class="ab-paragraph"
        :content="resolvedValue"
        :rules="rules"
        @click.native="onClick"
      ></MarkdownIt>
      <p v-else class="ab-paragraph">{{ $t('textElement.noValue') }}</p>
    </template>
    <template v-else>
      <p
        v-for="paragraph in paragraphs"
        :key="paragraph.id"
        class="ab-paragraph"
      >
        {{ paragraph.content }}
      </p>
      <p v-if="!paragraphs.length" class="ab-paragraph">
        {{ $t('textElement.noValue') }}
      </p>
    </template>
  </div>
</template>

<script>
import element from '@baserow/modules/builder/mixins/element'
import { generateHash } from '@baserow/modules/core/utils/hashing'
import { ensureString } from '@baserow/modules/core/utils/validator'
import { TEXT_FORMAT_TYPES } from '@baserow/modules/builder/enums'
import { prefixInternalResolvedUrl } from '@baserow/modules/builder/utils/urlResolution'

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
    TEXT_FORMAT_TYPES() {
      return TEXT_FORMAT_TYPES
    },
    // Custom rules to pass down to `MarkdownIt` element.
    // The goal is to make the styling of the rendered markdown content
    // consistent with the rest of the application builder CSS classes
    rules() {
      return {
        heading_open: (tokens, idx, options, env, renderer) => {
          const level = tokens[idx].markup.length
          tokens[idx].attrJoin('class', `ab-heading--h${level}`)
          return renderer.renderToken(tokens, idx, options)
        },
        link_open: (tokens, idx, options, env, renderer) => {
          const url = prefixInternalResolvedUrl(
            tokens[idx].attrGet('href'),
            this.builder,
            'custom',
            this.mode
          )
          tokens[idx].attrSet('href', url)
          tokens[idx].attrJoin('class', 'link-element__link')
          return renderer.renderToken(tokens, idx, options)
        },
        image: (tokens, idx, options, env, renderer) => {
          tokens[idx].attrJoin('class', 'image_element__img')
          return renderer.renderToken(tokens, idx, options)
        },
        paragraph_open: (tokens, idx, options, env, renderer) => {
          tokens[idx].attrJoin('class', 'ab-paragraph')
          return renderer.renderToken(tokens, idx, options)
        },
        table_open: (tokens, idx, options, env, renderer) => {
          tokens[idx].attrJoin('class', 'baserow-table')
          return renderer.renderToken(tokens, idx, options)
        },
        tr_open: (tokens, idx, options, env, renderer) => {
          // Only apply this styling to the first row present in table header.
          if (idx > 0 && tokens[idx - 1].type === 'thead_open') {
            tokens[idx].attrJoin('class', 'baserow-table__header-row')
          } else {
            tokens[idx].attrJoin('class', 'baserow-table__row')
          }
          return renderer.renderToken(tokens, idx, options)
        },
        th_open: (tokens, idx, options, env, renderer) => {
          tokens[idx].attrJoin('class', 'baserow-table__header-cell')
          return renderer.renderToken(tokens, idx, options)
        },
        td_open: (tokens, idx, options, env, renderer) => {
          tokens[idx].attrJoin('class', 'baserow-table__cell')
          return renderer.renderToken(tokens, idx, options)
        },
      }
    },
  },
  methods: {
    onClick(event) {
      if (this.mode === 'editing') {
        event.preventDefault()
        return
      }
      if (event.target.classList.contains('link-element__link')) {
        const url = event.target.getAttribute('href')

        if (url.startsWith('/')) {
          event.preventDefault()
          this.$router.push(url)
        }
      }
    },
  },
}
</script>
