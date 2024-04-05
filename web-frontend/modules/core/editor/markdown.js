import Markdown from 'markdown-it'
import taskLists from 'markdown-it-task-lists'

export const parseMarkdown = (markdown, { openLinkOnClick = false } = {}) => {
  const md = new Markdown({ html: false })
  md.use(taskLists, { label: true, enabled: true })

  if (!openLinkOnClick) {
    // Remove the href attribute from the link to avoid the user clicking on it.
    md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
      const hrefIndex = tokens[idx].attrIndex('href')
      if (hrefIndex >= 0) {
        tokens[idx].attrs.splice(hrefIndex, 1)
      }
      return self.renderToken(tokens, idx, options)
    }
  } else {
    // Add target="_blank" and rel="noopener noreferrer nofollow" to all links.
    md.renderer.rules.link_open = function (tokens, idx, options, env, self) {
      const targetIndex = tokens[idx].attrIndex('target')
      if (targetIndex < 0) {
        tokens[idx].attrPush(['target', '_blank'])
      }
      const relIndex = tokens[idx].attrIndex('rel')
      if (relIndex < 0) {
        tokens[idx].attrPush(['rel', 'noopener noreferrer nofollow'])
      }

      // Prevent container handlers from being called when clicking on a link.
      const onClickIndex = tokens[idx].attrIndex('onmousedown')
      if (onClickIndex < 0) {
        tokens[idx].attrPush([
          'onmousedown',
          '(function(event) { event.stopImmediatePropagation(); })(event)',
        ])
      }
      return self.renderToken(tokens, idx, options)
    }
  }

  return md.render(markdown)
}
