<template>
  <div class="control-elements">
    <div
      class="field-boolean-checkbox"
      :class="{ active: value }"
      @click="toggle(value)"
    >
      <i class="fas fa-check check"></i>
    </div>
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'

export default {
  mixins: [rowEditField],
  methods: {
    toggle(value) {
      const oldValue = !!value
      const newValue = !value
      this.$emit('update', newValue, oldValue)
    },
  },
}
</script>
