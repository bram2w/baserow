<template>
  <div
    class="rich-text-editor"
    :class="{ 'rich-text-editor--scrollbar-thin': thinScrollbar }"
  >
    <RichTextEditorMentionsList
      v-if="editable && enableMentions"
      ref="mentionsList"
      :show-search="false"
      :add-empty-item="false"
    />
    <div v-if="editable && enableRichTextFormatting">
      <RichTextEditorBubbleMenu
        v-show="bubbleMenuOpen"
        ref="bubbleMenu"
        :editor="editor"
      />
      <RichTextEditorFloatingMenu
        v-show="floatingMenuOpen"
        ref="floatingMenu"
        :editor="editor"
        :get-scrollable-area-bounding-rect="scrollableAreaBoundingRect"
      />
    </div>
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
import { TaskItem } from '@tiptap/extension-task-item'
import { TaskList } from '@tiptap/extension-task-list'
import { Text } from '@tiptap/extension-text'
import { mergeAttributes } from '@tiptap/core'

import { Markdown } from 'tiptap-markdown'

import RichTextEditorMentionsList from '@baserow/modules/core/components/editor/RichTextEditorMentionsList'
import RichTextEditorBubbleMenu from '@baserow/modules/core/components/editor/RichTextEditorBubbleMenu'
import RichTextEditorFloatingMenu from '@baserow/modules/core/components/editor/RichTextEditorFloatingMenu'
import EnterStopEditExtension from '@baserow/modules/core/components/editor/extensions/EnterStopEditExtension'
import suggestion from '@baserow/modules/core/editor/suggestion'
import { isElement } from '@baserow/modules/core/utils/dom'

const richTextEditorExtensions = [
  // Nodes
  Heading.configure({ levels: [1, 2, 3] }),
  ListItem,
  OrderedList,
  BulletList,
  CodeBlock,
  Blockquote,
  HorizontalRule,
  TaskItem,
  TaskList,
  // Marks
  Bold,
  Italic,
  Strike,
  Underline,
  Subscript,
  Superscript,
  // Extensions
  Markdown.configure({
    breaks: true,
  }),
]

export default {
  components: {
    EditorContent,
    RichTextEditorBubbleMenu,
    RichTextEditorMentionsList,
    RichTextEditorFloatingMenu,
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
    scrollableAreaElement: {
      type: Object,
      default: null,
    },
    thinScrollbar: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      editor: null,
      resizeObserver: null,
      bubbleMenuOpen: false,
      floatingMenuOpen: false,
    }
  },
  computed: {
    ...mapGetters({
      loggedUserId: 'auth/getUserId',
      workspace: 'workspace/getSelected',
    }),
    scrollableAreaBoundingRect() {
      if (this.scrollableAreaElement !== null) {
        return this.scrollableAreaElement.getBoundingClientRect()
      }
      return () => this.$el.getBoundingClientRect()
    },
  },
  watch: {
    editable: {
      handler(editable) {
        this.editor.setOptions({
          editable,
        })
        this.setupEditor()
      },
    },
    value(value) {
      if (!_.isEqual(value, this.editor.getJSON())) {
        this.editor.commands.setContent(value, false)
      }
    },
  },
  mounted() {
    const extensions = this.getConfiguredExtensions()
    this.createEditor(extensions)
  },
  unmount() {
    if (this.editor) {
      this.editor.destroy()
    }
    this.unregisterResizeObserver()
  },
  methods: {
    registerResizeObserver() {
      const resizeObserver = new ResizeObserver(() => {
        this.$refs.floatingMenu?.updateReferenceClientRect()
        this.bubbleMenuOpen = false
      })
      resizeObserver.observe(this.$el)
      this.resizeObserver = resizeObserver
    },
    unregisterResizeObserver() {
      if (this.resizeObserver) {
        this.resizeObserver.disconnect()
        this.resizeObserver = null
      }
    },
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
    createEditor(extensions) {
      this.editor = new Editor({
        content: this.value,
        editable: this.editable,
        extensions,
        onUpdate: () => {
          this.$emit('input', this.editor.getJSON())
        },
        onFocus: ({ editor, event }) => {
          if (this.editable && !this.bubbleMenuOpen) {
            this.floatingMenuOpen = true
          }
          this.$emit('focus')
        },
        onBlur: ({ editor, event }) => {
          if (this.isEventFromMenu(event)) {
            return // Do not emit blur event if the event is from one of the editor's menu.
          }

          this.bubbleMenuOpen = false
          this.floatingMenuOpen = false
          this.$emit('blur')
        },
        onSelectionUpdate: ({ editor }) => {
          if (this.editable && this.enableRichTextFormatting) {
            const hasValidSelection = editor.state.selection.empty === false
            const codeBlockActive = editor.isActive('codeBlock')

            if (hasValidSelection && !codeBlockActive) {
              this.bubbleMenuOpen = true
              this.floatingMenuOpen = false
            } else {
              this.bubbleMenuOpen = false
              this.floatingMenuOpen = true
            }
          }
        },
      })
      this.setupEditor()
    },
    setupEditor() {
      if (this.editable) {
        this.focus()
        this.floatingMenuOpen = true

        this.registerResizeObserver()
        this.registerAutoCollapseFloatingMenuHandler()
        this.registerAutoHideBubbleMenuHandler()
      } else {
        this.unregisterResizeObserver()
      }
    },
    registerAutoCollapseFloatingMenuHandler() {
      const $refs = this.$refs

      const handler = () => {
        $refs.floatingMenu?.collapse()
      }

      this.$el.addEventListener('mousedown', handler)
      this.$once('hook:unmounted', () => {
        this.$el.removeEventListener('mousedown', handler)
      })
    },
    registerAutoHideBubbleMenuHandler() {
      const _this = this

      const handler = (event) => {
        _this.bubbleMenuOpen = false
      }

      const elem = this.scrollableAreaElement ?? this.$el

      elem.addEventListener('scroll', handler)
      this.$once('hook:unmounted', () => {
        elem.removeEventListener('scroll', handler)
      })
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
    isEventFromMenu(event) {
      return (
        this.$refs.bubbleMenu?.isEventTargetInside(event) ||
        this.$refs.floatingMenu?.isEventTargetInside(event)
      )
    },
    isEventTargetInside(event) {
      return isElement(this.$el, event.target) || this.isEventFromMenu(event)
    },
  },
}
</script>
