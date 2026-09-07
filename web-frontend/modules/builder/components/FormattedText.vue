<template>
  <MarkdownIt
    v-if="isMarkdown"
    :content="text"
    :inline="markdownPreset.inline"
    :rules="markdownPreset.rules"
    :disabled-rules="markdownPreset.disabledRules"
    @click="onMarkdownClick"
  />
  <slot v-else name="plain" :text="text">{{ text }}</slot>
</template>

<script>
import { TEXT_FORMAT_TYPES } from '@baserow/modules/builder/enums'
import {
  MARKDOWN_PRESETS,
  createApplicationBuilderMarkdownPreset,
  handleMarkdownClick,
  splitTextMarker,
} from '@baserow/modules/builder/utils/markdown'

/**
 * Renders a user-provided text either as-is or as Markdown, using one of the
 * Application Builder rendering presets.
 *
 * The text renders as Markdown when the `format` prop says so (the Text element
 * keeps its own setting) or when the resolved text starts with the Markdown
 * marker, see `splitTextMarker`. The marker is stripped in both cases. Every
 * other surface passes only `content` and `preset`.
 *
 * The optional `plain` scoped slot customises the plain rendering, e.g. to keep
 * a styled wrapper around the text. The default is the bare text.
 *
 * `builder` and `mode` are needed to resolve internal links; they're injected
 * from the surrounding element by default, and can be passed explicitly by
 * consumers living outside an element (e.g. the toasts).
 */
export default {
  name: 'FormattedText',
  inject: {
    injectedBuilder: { from: 'builder', default: null },
    injectedMode: { from: 'mode', default: null },
  },
  props: {
    content: {
      type: [String, Number],
      required: false,
      default: '',
    },
    format: {
      type: String,
      required: false,
      default: TEXT_FORMAT_TYPES.PLAIN,
    },
    preset: {
      type: String,
      required: false,
      default: MARKDOWN_PRESETS.BLOCK,
      validator: (value) => Object.values(MARKDOWN_PRESETS).includes(value),
    },
    builder: {
      type: Object,
      required: false,
      default: null,
    },
    mode: {
      type: String,
      required: false,
      default: null,
    },
  },
  computed: {
    markedContent() {
      return splitTextMarker(this.content)
    },
    text() {
      return this.markedContent.text
    },
    isMarkdown() {
      return (
        this.format === TEXT_FORMAT_TYPES.MARKDOWN ||
        this.markedContent.format === TEXT_FORMAT_TYPES.MARKDOWN
      )
    },
    resolvedBuilder() {
      return this.builder || this.injectedBuilder
    },
    resolvedMode() {
      return this.mode || this.injectedMode
    },
    markdownPreset() {
      return createApplicationBuilderMarkdownPreset(this.preset, {
        builder: this.resolvedBuilder,
        mode: this.resolvedMode,
      })
    },
  },
  methods: {
    onMarkdownClick(event) {
      handleMarkdownClick(event, {
        mode: this.resolvedMode,
        router: this.$router,
      })
    },
  },
}
</script>
