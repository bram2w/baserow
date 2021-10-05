<template>
  <div class="control__elements">
    <input
      ref="input"
      v-model="copy"
      type="text"
      class="input input--large field-number"
      :class="{
        'input--error': (touched && !valid) || isInvalidNumber,
      }"
      :disabled="readOnly"
      @keyup.enter="$refs.input.blur()"
      @focus="select()"
      @blur="unselect()"
    />
    <div v-show="touched && !valid" class="error">
      {{ error }}
    </div>
    <div v-show="isInvalidNumber" class="error">Invalid Number</div>
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import rowEditFieldInput from '@baserow/modules/database/mixins/rowEditFieldInput'
import numberField from '@baserow/modules/database/mixins/numberField'

export default {
  mixins: [rowEditField, rowEditFieldInput, numberField],
  computed: {
    isInvalidNumber() {
      return this.copy === 'NaN'
    },
  },
}
</script>
