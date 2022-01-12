<template>
  <!-- eslint-disable-next-line vue/no-v-html -->
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
  },
  data() {
    return {
      htmlContent: '',
    }
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
  async created() {
    const Markdown = (await import('markdown-it')).default
    this.md = new Markdown()
    this.htmlContent = this.md.render(this.content)
  },
}
</script>
