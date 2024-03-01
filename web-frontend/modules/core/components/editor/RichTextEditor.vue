<template>
  <div>
    <RichTextEditorMentionsList
      v-if="enableMentions"
      ref="mentionsList"
      :show-search="false"
      :add-empty-item="false"
    />
    <EditorContent
      class="rich-text-editor__content"
      :class="[
        {
          'rich-text-editor__content--scaled': contentScaled,
        },
        editorClass,
      ]"
      :editor="editor"
    />
  </div>
</template>

<script>
import _ from 'lodash'
import { mapGetters } from 'vuex'
import { Editor, EditorContent } from '@tiptap/vue-2'
import { Placeholder } from '@tiptap/extension-placeholder'
import { Mention } from '@tiptap/extension-mention'
import { Document } from '@tiptap/extension-document'
import { Paragraph } from '@tiptap/extension-paragraph'
import { HardBreak } from '@tiptap/extension-hard-break'
import { Heading } from '@tiptap/extension-heading'
import { ListItem } from '@tiptap/extension-list-item'
import { BulletList } from '@tiptap/extension-bullet-list'
import { OrderedList } from '@tiptap/extension-ordered-list'
import { Bold } from '@tiptap/extension-bold'
import { Italic } from '@tiptap/extension-italic'
import { Strike } from '@tiptap/extension-strike'
import { Underline } from '@tiptap/extension-underline'
import { Subscript } from '@tiptap/extension-subscript'
import { Superscript } from '@tiptap/extension-superscript'
import { Blockquote } from '@tiptap/extension-blockquote'
import { CodeBlock } from '@tiptap/extension-code-block'
import { HorizontalRule } from '@tiptap/extension-horizontal-rule'
import { Text } from '@tiptap/extension-text'
import { Extension, mergeAttributes } from '@tiptap/core'
import { Plugin, PluginKey } from '@tiptap/pm/state'
import { Markdown } from 'tiptap-markdown'

import RichTextEditorMentionsList from '@baserow/modules/core/components/editor/RichTextEditorMentionsList'
import suggestion from '@baserow/modules/core/editor/suggestion'

const richTextEditorExtensions = [
  // Nodes
  Heading.configure({ levels: [1, 2, 3] }),
  ListItem,
  OrderedList,
  BulletList,
  CodeBlock,
  Blockquote,
  HorizontalRule,
  // Marks
  Bold,
  Italic,
  Strike,
  Underline,
  Subscript,
  Superscript,
  // Extensions
  Markdown,
]

// Please, note that we need to remap Enter to Shift-Enter for every extension
// relying on it in order to emit an event when the user presses Enter.
const EnterStopEditExtension = Extension.create({
  name: 'enterStopEditHandler',

  addOptions() {
    return {
      shiftKey: false,
    }
  },

  addProseMirrorPlugins() {
    return [
      new Plugin({
        key: new PluginKey('enterStopEditHandler'),
        props: {
          handleKeyDown: (view, event) => {
            const { doc } = view.state

            function isDocEmpty() {
              let isEmpty = true
              doc.descendants((node) => {
                const isContent =
                  node.type.name !== 'hardBreak' &&
                  !node.isText &&
                  !node.isBlock
                if (isContent || node.text?.trim()) {
                  isEmpty = false
                }
              })
              return isEmpty
            }

            if (
              event.key === 'Enter' &&
              event.shiftKey === this.options.shiftKey
            ) {
              if (!isDocEmpty()) {
                this.options.vueComponent.$emit('stop-edit')
              }
              return true
            }
            return false
          },
        },
      }),
    ]
  },
})

export default {
  components: {
    EditorContent,
    RichTextEditorMentionsList,
  },
  props: {
    value: {
      type: [Object, String],
      required: true,
    },
    placeholder: {
      type: String,
      default: null,
    },
    editable: {
      type: Boolean,
      default: true,
    },
    editorClass: {
      type: String,
      default: '',
    },
    contentScaled: {
      type: Boolean,
      default: false,
    },
    enableMentions: {
      type: Boolean,
      default: false,
    },
    enterStopEdit: {
      type: Boolean,
      default: false,
    },
    shiftEnterStopEdit: {
      type: Boolean,
      default: false,
    },
    enableRichTextFormatting: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      editor: null,
    }
  },
  computed: {
    ...mapGetters({
      loggedUserId: 'auth/getUserId',
      workspace: 'workspace/getSelected',
    }),
  },
  watch: {
    editable(editable) {
      this.editor.setOptions({
        editable,
      })
      this.editor.commands.focus('end')
    },
    value(value) {
      if (!_.isEqual(value, this.editor.getJSON())) {
        this.editor.commands.setContent(value, false)
      }
    },
  },
  mounted() {
    const extensions = this.getConfiguredExtensions()
    this.initTiptapEditor(extensions)
  },
  unmounted() {
    this.editor.destroy()
  },
  methods: {
    getConfiguredExtensions() {
      const extensions = [Document, Paragraph, Text, HardBreak]

      if (this.enableRichTextFormatting) {
        extensions.push(...richTextEditorExtensions)
      }

      if (this.enterStopEdit || this.shiftEnterStopEdit) {
        const enterKeyExt = EnterStopEditExtension.configure({
          vueComponent: this,
          shiftKey: this.shiftEnterStopEdit,
        })
        extensions.push(enterKeyExt)
      }
      if (this.enableMentions) {
        const renderHTML = this.customRenderHTMLForMentions()
        const mentionsExt = Mention.configure({
          renderHTML,
          suggestion: suggestion({
            component: this.$refs.mentionsList,
          }),
        })
        extensions.push(mentionsExt)
      }

      if (this.placeholder) {
        extensions.push(
          Placeholder.configure({
            placeholder: this.placeholder,
          })
        )
      }
      return extensions
    },
    initTiptapEditor(extensions) {
      this.editor = new Editor({
        content: this.value,
        editable: this.editable,
        extensions,
        onUpdate: () => {
          this.$emit('input', this.editor.getJSON())
        },
        onFocus: () => {
          this.$emit('focus')
        },
        onBlur: () => {
          this.$emit('blur')
        },
      })

      if (this.editable && this.enableRichTextFormatting) {
        this.editor.commands.unsetAllMarks()
      }
    },
    customRenderHTMLForMentions() {
      const loggedUserId = this.loggedUserId
      const isUserInWorkspace =
        this.$store.getters['workspace/isUserIdMemberOfSelectedWorkspace']
      return ({ node, options }) => {
        let className = 'rich-text-editor__mention'
        if (node.attrs.id === loggedUserId) {
          className += ' rich-text-editor__mention--current-user'
        } else if (!isUserInWorkspace(node.attrs.id)) {
          className += ' rich-text-editor__mention--user-gone'
        }
        return [
          'span',
          mergeAttributes({ class: className }, this.HTMLAttributes),
          `${options.suggestion.char}${node.attrs.label ?? node.attrs.id}`,
        ]
      }
    },
    focus() {
      this.editor.commands.focus('end')
    },
    serializeToMarkdown() {
      return this.editor.storage.markdown.getMarkdown()
    },
  },
}
</script>
