<template>
  <div
    class="grid-view-cell"
    :class="{
      active: selected,
      editing: editing,
      invalid: editing && !isValid(),
    }"
  >
    <div v-show="!editing" class="grid-field-number">{{ value }}</div>
    <template v-if="editing">
      <input
        ref="input"
        v-model="copy"
        type="text"
        class="grid-field-number-input"
      />
      <div v-show="!isValid()" class="grid-view-cell-error align-right">
        {{ getError() }}
      </div>
    </template>
  </div>
</template>

<script>
import gridField from '@baserow/modules/database/mixins/gridField'
import gridFieldInput from '@baserow/modules/database/mixins/gridFieldInput'

export default {
  mixins: [gridField, gridFieldInput],
  methods: {
    getError() {
      if (this.copy === null || this.copy === '') {
        return null
      }
      if (isNaN(parseFloat(this.copy)) || !isFinite(this.copy)) {
        return 'Invalid number'
      }
      return null
    },
    isValid() {
      return this.getError() === null
    },
    afterEdit() {
      this.$nextTick(() => {
        this.$refs.input.focus()
        this.$refs.input.selectionStart = this.$refs.input.selectionEnd = 100000
      })
    },
    beforeSave(value) {
      if (value === '' || isNaN(value) || value === undefined) {
        return null
      }
      const decimalPlaces =
        this.field.number_type === 'DECIMAL'
          ? this.field.number_decimal_places
          : 0
      let number = parseFloat(value)
      if (!this.field.number_negative && number < 0) {
        number = 0
      }
      return number.toFixed(decimalPlaces)
    },
  },
}
</script>
