<script>
import Markdown from 'markdown-it'
import taskLists from 'markdown-it-task-lists'

export default {
  functional: true,
  render(createElement, context) {
    const { props } = context
    const md = new Markdown({ html: true })

    function parseMarkdown(value) {
      return md.use(taskLists, { label: true, enabled: true }).render(value)
    }

    // Take only a part of the text as a preview to avoid rendering a huge amount of
    // HTML that could slow down the page and won't be visible anyway
    let preview = ''
    if (props.value) {
      preview = props.value.substring(0, 200)
      if (props.value.length > 200) {
        preview += '...'
      }
    }

    return createElement('div', {
      class:
        'grid-view__cell grid-field-rich-text__cell grid-field-rich-text__cell--preview',
      domProps: {
        innerHTML: parseMarkdown(preview),
      },
    })
  },
}
</script>
