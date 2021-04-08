<template>
  <Checkbox :value="copy" :disabled="readOnly" @input="input($event)">
    Selected
  </Checkbox>
</template>

<script>
import { trueString } from '@baserow/modules/database/utils/constants'

export default {
  name: 'ViewFilterTypeBoolean',
  props: {
    value: {
      type: String,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    copy() {
      const value = this.value.toLowerCase().trim()
      return trueString.includes(value)
    },
  },
  methods: {
    input(value) {
      this.$emit('input', value ? '1' : '0')
    },
  },
}
</script>
