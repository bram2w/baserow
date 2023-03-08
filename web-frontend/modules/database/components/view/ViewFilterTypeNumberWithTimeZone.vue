<template>
  <div class="filters__multi-value">
    <input
      ref="input"
      v-model="xAgo"
      type="text"
      class="
        input
        filters__combined_value-input
        filters__value-input
        filters__value-input--small
      "
      :class="{ 'input--error': $v.xAgo.$error }"
      :disabled="disabled"
      @input="
        ;[
          setCopy($event.target.value),
          delayedUpdate($event.target.value, true),
        ]
      "
      @keydown.enter="
        ;[
          setCopy($event.target.value),
          delayedUpdate($event.target.value, true),
        ]
      "
    />
    <span class="filters__value-timezone">{{ getTimezoneAbbr() }}</span>
  </div>
</template>

<script>
import { integer, required } from 'vuelidate/lib/validators'
import filterTypeDateInput from '@baserow/modules/database/mixins/filterTypeDateInput'

export default {
  name: 'ViewFilterTypeNumberWithTimeZone',
  mixins: [filterTypeDateInput],
  data() {
    return {
      xAgo: '',
    }
  },
  methods: {
    isInputValid() {
      return !this.$v.xAgo.$error
    },
    setCopy(value, sender) {
      const [, xAgo] = this.splitCombinedValue(value)
      this.xAgo = xAgo
    },
  },
  validations: {
    copy: { required },
    xAgo: { integer },
  },
}
</script>
