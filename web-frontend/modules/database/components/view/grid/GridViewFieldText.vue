<template>
  <div
    ref="cell"
    class="grid-view-cell"
    :class="{ active: selected, editing: editing }"
  >
    <div v-show="!editing" class="grid-field-text">{{ value }}</div>
    <input
      v-if="editing"
      ref="input"
      v-model="copy"
      type="text"
      class="grid-field-text-input"
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
  },
}
</script>
