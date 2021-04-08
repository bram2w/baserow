<template>
  <div
    class="grid-view__cell active"
    :class="{
      editing: editing,
      invalid: editing && !isValid(),
    }"
    @contextmenu="stopContextIfEditing($event)"
  >
    <div v-show="!editing" class="grid-field-text">
      <a :href="value" target="_blank">{{ value }}</a>
    </div>
    <template v-if="editing">
      <input
        ref="input"
        v-model="copy"
        type="text"
        class="grid-field-text__input"
      />
      <div v-show="!isValid()" class="grid-view__cell--error align-right">
        {{ getError() }}
      </div>
    </template>
  </div>
</template>

<script>
import gridField from '@baserow/modules/database/mixins/gridField'
import gridFieldInput from '@baserow/modules/database/mixins/gridFieldInput'
import URLField from '@baserow/modules/database/mixins/URLField'

export default {
  mixins: [gridField, gridFieldInput, URLField],
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
