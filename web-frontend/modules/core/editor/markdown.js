import Markdown from 'markdown-it'
import taskLists from 'markdown-it-task-lists'

const md = new Markdown({ html: false })
md.use(taskLists, { label: true, enabled: true })

export const defaultMarkdownParser = md
export const parseMarkdown = (markdown) => md.render(markdown)
