<template>
  <div class="filters__multi-value">
    <input
      ref="input"
      v-model="copy"
      type="text"
      class="
        input
        filters__combined_value-input
        filters__value-input
        filters__value-input--small
      "
      :class="{ 'input--error': $v.copy.$error }"
      :disabled="disabled"
      @input="combinedDelayedUpdate($event.target.value)"
      @keydown.enter="combinedDelayedUpdate($event.target.value, true)"
    />
    <span class="filters__value-timezone">{{ timezoneValue }}</span>
  </div>
</template>

<script>
import viewFilter from '@baserow/modules/database/mixins/viewFilter'
import { integer } from 'vuelidate/lib/validators'

import filterTypeInput from '@baserow/modules/database/mixins/filterTypeInput'

export default {
  name: 'ViewFilterTypeNumberWithTimeZone',
  mixins: [filterTypeInput, viewFilter],
  computed: {
    timezoneValue() {
      const [timezone] = this.splitCombinedValue(this.filter.value)
      return timezone
    },
  },
  watch: {
    'filter.value'(value) {
      this.copy = this.getDaysAgo(value)
    },
  },
  created() {
    this.copy = this.getDaysAgo(this.filter.value)
  },
  methods: {
    getSeparator() {
      return '?'
    },
    splitCombinedValue(value) {
      const separator = this.getSeparator()
      const [timezone, daysAgo] = value.split(separator)
      return [timezone, daysAgo]
    },
    getDaysAgo(value) {
      const [, daysAgo] = this.splitCombinedValue(value)
      return daysAgo
    },
    prepareValue(timezoneValue, daysAgo) {
      const separator = this.getSeparator()
      return `${timezoneValue}${separator}${daysAgo}`
    },
    combinedDelayedUpdate(value, immediately = false) {
      const preparedValue = this.prepareValue(this.timezoneValue, value)
      return this.delayedUpdate(preparedValue, immediately)
    },
    focus() {
      this.$refs.input.focus()
    },
  },
  validations: {
    copy: { integer },
  },
}
</script>
