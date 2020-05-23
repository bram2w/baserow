<template>
  <div
    ref="cell"
    class="grid-view-cell grid-view-cell--long-text"
    :class="{ active: selected, editing: editing }"
    @contextmenu="stopContextIfEditing($event)"
  >
    <div v-show="!editing" class="grid-field-long-text">{{ value }}</div>
    <textarea
      v-prevent-parent-scroll
      v-if="editing"
      ref="input"
      v-model="copy"
      type="text"
      class="grid-field-long-text-textarea"
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
