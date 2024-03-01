<template>
  <div
    ref="cell"
    class="grid-view__cell grid-field-long-text__cell active"
    :class="{ editing: opened }"
    @contextmenu="stopContextIfEditing($event)"
  >
    <div v-prevent-parent-scroll="opened && editing" :class="classNames">
      <RichTextEditor
        ref="input"
        v-model="richCopy"
        :editable="editing"
        :content-scaled="!opened || !editing"
        :enable-rich-text-formatting="true"
      ></RichTextEditor>
    </div>
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
        return 'grid-field-long-text'
      } else if (this.editing) {
        return 'grid-field-long-text__textarea grid-field-long-text__textarea--rich-editor'
      } else {
        return 'grid-field-long-text__textarea'
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
  },
}
</script>
