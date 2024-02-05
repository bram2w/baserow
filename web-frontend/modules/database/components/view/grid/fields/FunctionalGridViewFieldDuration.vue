<template functional>
  <div ref="cell" class="grid-view__cell" :class="data.staticClass || ''">
    <div class="grid-field-duration">
      {{ $options.methods.formatValue(props.field, props.value) }}
    </div>
  </div>
</template>

<script>
import { formatDurationValue } from '@baserow/modules/database/utils/duration'

export default {
  name: 'FunctionalGridViewFieldDuration',
  functional: true,
  methods: {
    formatValue(field, value) {
      return formatDurationValue(value, field.duration_format)
    },
  },
}
</script>
