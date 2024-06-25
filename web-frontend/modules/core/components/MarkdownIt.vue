<template>
  <!-- eslint-disable-next-line vue/no-v-html vue/no-v-text-v-html-on-component -->
  <component :is="tag" class="markdown" v-html="htmlContent" />
</template>

<script>
export default {
  name: 'MarkdownIt',
  props: {
    content: {
      required: true,
      type: String,
    },
    tag: {
      required: false,
      type: String,
      default: 'div',
    },
    rules: {
      required: false,
      type: Object,
      default: () => {},
    },
  },
  data() {
    return {
      htmlContent: '',
    }
  },
  async fetch() {
    const Markdown = (await import('markdown-it')).default
    this.md = new Markdown()
    this.md.renderer.rules = { ...this.md.renderer.rules, ...this.rules }
    this.htmlContent = this.md.render(this.content)
  },
  computed: {
    // Makes content watchable
    localContent() {
      return this.content
    },
  },
  watch: {
    localContent(newValue) {
      if (this.md) {
        this.htmlContent = this.md.render(newValue)
      }
    },
  },
}
</script>
