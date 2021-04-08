<template>
  <input
    ref="input"
    v-model="copy"
    type="text"
    class="input filters__value-input"
    :class="{ 'input--error': $v.copy.$error }"
    :disabled="readOnly"
    @input="delayedUpdate($event.target.value)"
    @keydown.enter="delayedUpdate($event.target.value, true)"
  />
</template>

<script>
import filterTypeInput from '@baserow/modules/database/mixins/filterTypeInput'

export default {
  name: 'ViewFilterTypeText',
  mixins: [filterTypeInput],
  methods: {
    focus() {
      this.$refs.input.focus()
    },
  },
}
</script>
