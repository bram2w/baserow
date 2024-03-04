<template>
  <div
    ref="cell"
    v-prevent-parent-scroll="opened && editing"
    class="grid-view__cell grid-field-long-text__cell active"
    :class="{ editing: opened }"
    @contextmenu="stopContextIfEditing($event)"
  >
    <RichTextEditor
      ref="input"
      v-model="richCopy"
      :class="classNames"
      :editable="editing"
      :content-scaled="!opened || !editing"
      :enable-rich-text-formatting="true"
      :thin-scrollbar="true"
    ></RichTextEditor>
  </div>
</template>

<script>
import RichTextEditor from '@baserow/modules/core/components/editor/RichTextEditor.vue'
import gridField from '@baserow/modules/database/mixins/gridField'
import gridFieldInput from '@baserow/modules/database/mixins/gridFieldInput'

export default {
  components: { RichTextEditor },
  mixins: [gridField, gridFieldInput],
  data() {
    return {
      // local copy of the value storing the JSON representation of the rich text editor
      richCopy: '',
    }
  },
  computed: {
    classNames() {
      if (!this.opened) {
        return 'grid-field-rich-text'
      } else if (this.editing) {
        return 'grid-field-rich-text__textarea grid-field-rich-text__textarea--rich-editor'
      } else {
        return 'grid-field-rich-text__textarea'
      }
    },
  },
  watch: {
    value: {
      handler(value) {
        this.richCopy = value || ''
      },
      immediate: true,
    },
    editing(editing) {
      if (!editing) {
        this.richCopy = this.value || ''
      }
    },
  },
  methods: {
    scrollHeight() {
      return {
        sh: this.$refs.container.scrollHeight,
        st: this.$refs.container.scrollTop,
      }
    },
    cancel() {
      return this.save()
    },
    beforeSave() {
      return this.$refs.input.serializeToMarkdown()
    },
    afterEdit() {
      this.$nextTick(() => {
        this.$refs.input.focus()
      })
    },
    canSaveByPressingEnter(event) {
      return false
    },
    canUnselectByClickingOutside(event) {
      // The RichTextEditorBubbleMenuContext component is a context menu and so it's not
      // a direct child of the RichTextEditorBubbleMenu component. This means that the
      // when you click on an item, we have to prevent the next unselect event from
      // happening otherwise the cell will lose focus and the editor will close.
      if (this.editing && this.preventNextUnselect) {
        this.preventNextUnselect = false
        return false
      }

      return !this.editing || !this.$refs.input?.isEventTargetInside(event)
    },
  },
}
</script>
