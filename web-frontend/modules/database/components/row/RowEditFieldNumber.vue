<template>
  <FormGroup :error="(touched && !valid) || isInvalidNumber">
    <FormInput
      ref="input"
      v-model="copy"
      size="large"
      :error="(touched && !valid) || isInvalidNumber"
      :disabled="readOnly"
      @keyup.enter="$refs.input.blur()"
      @focus="select()"
      @blur="unselect()"
    />

    <template #error>
      <span v-show="touched && !valid">
        {{ error }}
      </span>
      <span v-show="isInvalidNumber">Invalid Number</span>
    </template>
  </FormGroup>
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
