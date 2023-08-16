<template>
  <Alert v-if="isFormulaInvalid" type="error" minimal>
    <div class="margin-bottom-1">
      {{ $t('formulaInputField.errorInvalidFormula') }}
    </div>
    <Button
      class="button formula-input-field__reset-button"
      type="error"
      size="tiny"
      @click="reset"
    >
      {{ $t('action.reset') }}
    </Button>
  </Alert>
  <EditorContent
    v-else
    class="input formula-input-field"
    :class="classes"
    :editor="editor"
  />
</template>

<script>
import { Editor, EditorContent, generateHTML, Node } from '@tiptap/vue-2'
import { Placeholder } from '@tiptap/extension-placeholder'
import { Document } from '@tiptap/extension-document'
import { Text } from '@tiptap/extension-text'
import _ from 'lodash'
import parseBaserowFormula from '@baserow/formula/parser/parser'
import { ToTipTapVisitor } from '@baserow/modules/core/formula/toTipTapVisitor'
import { RuntimeFunctionCollection } from '@baserow/modules/core/functionCollection'
import { FromTipTapVisitor } from '@baserow/modules/core/formula/fromTipTapVisitor'
import { mergeAttributes } from '@tiptap/core'
import { HardBreak } from '@tiptap/extension-hard-break'

export default {
  name: 'FormulaInputField',
  components: {
    EditorContent,
  },
  props: {
    value: {
      type: String,
      default: '',
    },
    placeholder: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      editor: null,
      content: null,
      isFocused: false,
      isFormulaInvalid: false,
    }
  },
  computed: {
    classes() {
      return {
        'formula-input-field--focused': this.isFocused,
      }
    },
    placeHolderExt() {
      return Placeholder.configure({
        placeholder: this.placeholder,
      })
    },
    hardBreakExt() {
      return HardBreak.extend({
        addKeyboardShortcuts() {
          return {
            Enter: () => this.editor.commands.setHardBreak(),
          }
        },
      })
    },
    formulaComponents() {
      return Object.values(this.$registry.getAll('runtimeFormulaFunction'))
        .map((type) => type.formulaComponent)
        .filter((component) => component !== null)
    },
    wrapperNode() {
      return Node.create({
        name: 'wrapper',
        group: 'block',
        content: 'inline*',
        parseHTML() {
          return [{ tag: 'span' }]
        },
        renderHTML({ HTMLAttributes }) {
          return ['span', mergeAttributes(HTMLAttributes), 0]
        },
      })
    },
    extensions() {
      const DocumentNode = Document.extend()
      const TextNode = Text.extend({ inline: true })

      return [
        DocumentNode,
        this.wrapperNode,
        TextNode,
        this.placeHolderExt,
        this.hardBreakExt,
        ...this.formulaComponents,
      ]
    },
    htmlContent() {
      return generateHTML(this.content, this.extensions)
    },
    wrapperContent() {
      return this.editor.getJSON().content[0].content
    },
  },
  watch: {
    value(value) {
      if (!_.isEqual(value, this.toFormula(this.wrapperContent))) {
        const content = this.toContent(value)

        if (!this.isFormulaInvalid) {
          this.content = content
        }
      }
    },
    content: {
      handler() {
        if (!_.isEqual(this.content, this.editor.getJSON())) {
          this.editor?.commands.setContent(this.htmlContent, false, {
            preserveWhitespace: 'full',
          })
        }
      },
      deep: true,
    },
  },
  mounted() {
    this.content = this.toContent(this.value)
    this.editor = new Editor({
      content: this.htmlContent,
      editable: true,
      onUpdate: this.onUpdate,
      onFocus: this.onFocus,
      onBlur: this.onBlur,
      extensions: this.extensions,
      parseOptions: {
        preserveWhitespace: 'full',
      },
    })
  },
  beforeDestroy() {
    this.editor?.destroy()
  },
  methods: {
    reset() {
      this.isFormulaInvalid = false
      this.$emit('input', '')
    },
    onUpdate() {
      this.fixMultipleWrappers()

      if (!this.isFormulaInvalid) {
        this.$emit('input', this.toFormula(this.wrapperContent))
      }
    },
    onFocus() {
      this.isFocused = true
    },
    onBlur() {
      this.isFocused = false
    },
    toContent(formula) {
      if (_.isEmpty(formula)) {
        return {
          type: 'doc',
          content: [{ type: 'wrapper', content: [] }],
        }
      }

      try {
        const tree = parseBaserowFormula(formula)
        const functionCollection = new RuntimeFunctionCollection(this.$registry)
        const content = new ToTipTapVisitor(functionCollection).visit(tree)

        return {
          type: 'doc',
          content: [{ type: 'wrapper', content }],
        }
      } catch (error) {
        this.isFormulaInvalid = true
        return null
      }
    },
    toFormula(content) {
      const functionCollection = new RuntimeFunctionCollection(this.$registry)
      try {
        return new FromTipTapVisitor(functionCollection).visit(content || [])
      } catch (error) {
        this.isFormulaInvalid = true
        return null
      }
    },
    /**
     * Sometimes TipTap will insert a new wrapper by itself. For example when you add
     * text in front of a custom component it will create a separate wrapper for that
     * text. This is annoying behaviour since we only want to deal with one wrapper
     * and not multiple.
     *
     * This function checks if there are multiple wrappers and if so, combines them
     * into one. That action is seamless to the user and won't interfere with the typing
     */
    fixMultipleWrappers() {
      if (this.editor.getJSON().content.length > 1) {
        this.editor.commands.joinForward()
      }
    },
  },
}
</script>
