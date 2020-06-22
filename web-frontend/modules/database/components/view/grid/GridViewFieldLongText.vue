<template>
  <div
    ref="cell"
    class="grid-view__cell grid-field-long-text__cell"
    :class="{ active: selected, editing: editing }"
    @contextmenu="stopContextIfEditing($event)"
  >
    <div v-show="!editing" class="grid-field-long-text">{{ value }}</div>
    <textarea
      v-if="editing"
      ref="input"
      v-model="copy"
      v-prevent-parent-scroll
      type="text"
      class="grid-field-long-text__textarea"
    />
  </div>
</template>

<script>
import gridField from '@baserow/modules/database/mixins/gridField'
import gridFieldInput from '@baserow/modules/database/mixins/gridFieldInput'

export default {
  mixins: [gridField, gridFieldInput],
  methods: {
    afterEdit() {
      this.$nextTick(() => {
        this.$refs.input.focus()
        this.$refs.input.selectionStart = this.$refs.input.selectionEnd = 100000
      })
    },
    canSaveByPressingEnter() {
      return false
    },
  },
}
</script>
