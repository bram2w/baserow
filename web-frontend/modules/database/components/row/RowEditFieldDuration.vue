<template>
  <div class="control__elements">
    <input
      ref="input"
      v-model="formattedValue"
      :placeholder="field.duration_format"
      type="text"
      class="input field-duration"
      :class="{
        'input--error': touched && !valid,
      }"
      :disabled="readOnly"
      @keypress="onKeyPress(field, $event)"
      @keyup.enter="$refs.input.blur()"
      @keyup="updateCopy(field, $event.target.value)"
      @focus="select()"
      @blur="unselect()"
    />
    <div v-show="touched && !valid" class="error">
      {{ error }}
    </div>
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import rowEditFieldInput from '@baserow/modules/database/mixins/rowEditFieldInput'
import durationField from '@baserow/modules/database/mixins/durationField'

export default {
  mixins: [rowEditField, rowEditFieldInput, durationField],
  watch: {
    'field.duration_format': {
      handler() {
        this.updateCopy(this.field, this.value)
        this.updateFormattedValue(this.field, this.copy)
      },
    },
    value: {
      handler(newValue) {
        this.updateCopy(this.field, newValue)
        this.updateFormattedValue(this.field, this.copy)
      },
    },
  },
}
</script>
