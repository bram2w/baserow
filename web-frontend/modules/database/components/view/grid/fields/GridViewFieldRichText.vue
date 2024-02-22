<template>
  <div
    ref="cell"
    class="grid-view__cell grid-field-long-text__cell active"
    :class="{ editing: opened }"
    @contextmenu="stopContextIfEditing($event)"
  >
    <div v-if="!opened" class="grid-field-long-text">
      {{ value }}
    </div>
    <div
      v-else-if="editing"
      v-prevent-parent-scroll
      class="grid-field-long-text__textarea"
    >
      <RichTextEditor
        ref="input"
        v-model="richCopy"
        :enable-rich-text-formatting="true"
      ></RichTextEditor>
    </div>
    <div v-else class="grid-field-long-text__textarea">
      {{ richCopy }}
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
  watch: {
    value: {
      handler(value) {
        this.richCopy = value || ''
      },
      immediate: true,
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
