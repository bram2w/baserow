<template>
  <div class="control__elements">
    <RichTextEditor
      ref="input"
      v-model="richCopy"
      class="input field-rich-text"
      :class="{ 'input--error': touched && !valid, active: editing }"
      :disabled="readOnly"
      :editable="!readOnly"
      :enable-rich-text-formatting="true"
      @focus="select()"
      @blur="unselect()"
    ></RichTextEditor>

    <div v-show="touched && !valid" class="error">
      {{ error }}
    </div>
  </div>
</template>

<script>
import RichTextEditor from '@baserow/modules/core/components/editor/RichTextEditor.vue'
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import rowEditFieldInput from '@baserow/modules/database/mixins/rowEditFieldInput'

export default {
  components: { RichTextEditor },
  mixins: [rowEditField, rowEditFieldInput],
  data() {
    return {
      // local copy of the value storing the JSON representation of the rich text editor
      richCopy: '',
    }
  },
  created() {
    this.richCopy = this.value || ''
  },
  methods: {
    beforeSave() {
      return this.$refs.input.serializeToMarkdown()
    },
  },
}
</script>
