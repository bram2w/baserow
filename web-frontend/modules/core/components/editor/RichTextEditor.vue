<template>
  <div>
    <RichTextEditorMentionsList
      ref="mentionsList"
      :show-search="false"
      :add-empty-item="false"
    />
    <EditorContent :editor="editor" />
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
import { Text } from '@tiptap/extension-text'
import { Extension, mergeAttributes } from '@tiptap/core'
import { Plugin, PluginKey } from '@tiptap/pm/state'

import RichTextEditorMentionsList from '@baserow/modules/core/components/editor/RichTextEditorMentionsList'
import suggestion from '@baserow/modules/core/editor/suggestion'

// Please, note that we need to remap Enter to Shift-Enter for every extension
// relying on it in order to emit an event when the user presses Enter.
const EnterKeyExtension = Extension.create({
  name: 'enterKeyEventHandler',

  addProseMirrorPlugins() {
    return [
      new Plugin({
        key: new PluginKey('enterKeyEventHandler'),
        props: {
          handleKeyDown: (view, event) => {
            const { doc } = view.state

            function isDocEmpty() {
              let isEmpty = true
              doc.descendants((node) => {
                const textNodes = ['text', 'paragraph', 'hardBreak']
                if (!textNodes.includes(node.type.name) || node.text?.trim()) {
                  isEmpty = false
                }
              })
              return isEmpty
            }

            if (event.key === 'Enter' && !event.shiftKey) {
              if (!isDocEmpty()) {
                this.options.vueComponent.$emit('entered')
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
      isUserIdMemberOfSelectedWorkspace:
        'workspace/isUserIdMemberOfSelectedWorkspace',
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
      const jsonContent = this.editor.getJSON()

      if (_.isEqual(jsonContent, value)) {
        return
      }

      this.editor.commands.setContent(value, false)
    },
  },
  mounted() {
    const loggedUserId = this.loggedUserId
    const originalRenderHTML = Mention.config.renderHTML
    const isUserInWorkspace =
      this.$store.getters['workspace/isUserIdMemberOfSelectedWorkspace']
    const mentionsExt = Mention.extend({
      renderHTML({ node, HTMLAttributes }) {
        let className = 'rich-text-editor__mention'
        if (node.attrs.id === loggedUserId) {
          className += ' rich-text-editor__mention--current-user'
        } else if (!isUserInWorkspace(node.attrs.id)) {
          className += ' rich-text-editor__mention--user-gone'
        }
        return originalRenderHTML.call(this, {
          node,
          HTMLAttributes: mergeAttributes(HTMLAttributes, { class: className }),
        })
      },
    }).configure({
      suggestion: suggestion({
        component: this.$refs.mentionsList,
      }),
    })
    const enterKeyExt = EnterKeyExtension.configure({ vueComponent: this })
    const extensions = [
      Document,
      Paragraph,
      Text,
      HardBreak,
      enterKeyExt,
      mentionsExt,
    ]
    if (this.placeholder) {
      extensions.push(
        Placeholder.configure({
          placeholder: this.placeholder,
        })
      )
    }
    this.editor = new Editor({
      content: this.value,
      editable: this.editable,
      editorProps: {
        attributes: {
          class: this.editable ? 'rich-text-editor' : null,
        },
      },
      extensions,
      onUpdate: () => {
        this.$emit('input', this.editor.getJSON())
      },
    })
  },
  beforeDestroy() {
    this.editor.destroy()
  },
}
</script>
