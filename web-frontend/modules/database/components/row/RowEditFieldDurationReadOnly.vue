<template>
  <div class="control__elements">
    <div>{{ formattedValue }}</div>
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import durationField from '@baserow/modules/database/mixins/durationField'

export default {
  mixins: [rowEditField, durationField],
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
