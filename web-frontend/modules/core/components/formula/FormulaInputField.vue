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
  <div v-else>
    <EditorContent
      ref="editor"
      class="input formula-input-field"
      :class="classes"
      :editor="editor"
      @data-component-clicked="dataComponentClicked"
    />
    <DataExplorer
      ref="dataExplorer"
      :nodes="nodes"
      :node-selected="nodeSelected"
      :loading="dataExplorerLoading"
      @node-selected="dataExplorerItemSelected"
      @node-toggled="editor.commands.focus()"
    ></DataExplorer>
  </div>
</template>

<script>
import { Editor, EditorContent, generateHTML, Node } from '@tiptap/vue-2'
import { Placeholder } from '@tiptap/extension-placeholder'
import { Document } from '@tiptap/extension-document'
import { Text } from '@tiptap/extension-text'
import _ from 'lodash'
import parseBaserowFormula from '@baserow/modules/core/formula/parser/parser'
import { ToTipTapVisitor } from '@baserow/modules/core/formula/tiptap/toTipTapVisitor'
import { RuntimeFunctionCollection } from '@baserow/modules/core/functionCollection'
import { FromTipTapVisitor } from '@baserow/modules/core/formula/tiptap/fromTipTapVisitor'
import { mergeAttributes } from '@tiptap/core'
import { HardBreak } from '@tiptap/extension-hard-break'
import DataExplorer from '@baserow/modules/core/components/dataExplorer/DataExplorer'
import { onClickOutside } from '@baserow/modules/core/utils/dom'
import { RuntimeGet } from '@baserow/modules/core/runtimeFormulaTypes'

export default {
  name: 'FormulaInputField',
  components: {
    DataExplorer,
    EditorContent,
  },
  provide() {
    // Provide the application context to all formula components
    return { applicationContext: this.applicationContext }
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
    dataProviders: {
      type: Array,
      required: false,
      default: () => [],
    },
    dataExplorerLoading: {
      type: Boolean,
      required: false,
      default: false,
    },
    applicationContext: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      editor: null,
      content: null,
      isFocused: false,
      isFormulaInvalid: false,
      dataNodeSelected: null,
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
    nodes() {
      return this.dataProviders
        .map((dataProvider) => dataProvider.getNodes(this.applicationContext))
        .filter((dataProviderNodes) => dataProviderNodes.nodes?.length > 0)
    },
    nodeSelected() {
      return this.dataNodeSelected?.attrs?.path || null
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
      extensions: this.extensions,
      parseOptions: {
        preserveWhitespace: 'full',
      },
      editorProps: {
        handleClick: this.unSelectNode,
      },
    })

    const clickOutsideEventCancel = onClickOutside(this.$el, this.onBlur)
    this.$once('hook:beforeDestroy', clickOutsideEventCancel)
  },
  beforeDestroy() {
    this.editor?.destroy()
  },
  methods: {
    reset() {
      this.isFormulaInvalid = false
      this.$emit('input', '')
    },
    emitChange() {
      if (!this.isFormulaInvalid) {
        this.$emit('input', this.toFormula(this.wrapperContent))
      }
    },
    onUpdate() {
      this.fixMultipleWrappers()
      this.unSelectNode()
      this.emitChange()
    },
    onFocus() {
      if (!this.isFocused) {
        this.isFocused = true
        this.unSelectNode()
        this.$refs.dataExplorer.show(
          this.$refs.editor.$el,
          'bottom',
          'left',
          -100,
          -330
        )
      }
    },
    onBlur(target) {
      if (
        !this.$refs.dataExplorer.$el.contains(target) &&
        !this.$refs.editor.$el.contains(target)
      ) {
        this.isFocused = false
        this.$refs.dataExplorer.hide()
        this.unSelectNode()
      }
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
    dataComponentClicked(node) {
      this.selectNode(node)
      this.editor.commands.blur()
    },
    dataExplorerItemSelected({ path }) {
      const isInEditingMode = this.dataNodeSelected !== null
      if (isInEditingMode) {
        this.dataNodeSelected.attrs.path = path
        this.emitChange()
      } else {
        const getNode = new RuntimeGet().toNode([{ text: path }])
        this.editor.commands.insertContent(getNode)
      }
      this.editor.commands.focus()
    },
    selectNode(node) {
      if (node) {
        this.unSelectNode()
        this.dataNodeSelected = node
        this.dataNodeSelected.attrs.isSelected = true
      }
    },
    unSelectNode() {
      if (this.dataNodeSelected) {
        this.dataNodeSelected.attrs.isSelected = false
        this.dataNodeSelected = null
      }
    },
  },
}
</script>
