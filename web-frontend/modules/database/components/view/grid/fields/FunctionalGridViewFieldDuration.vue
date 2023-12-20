<template functional>
  <div ref="cell" class="grid-view__cell" :class="data.staticClass || ''">
    <div class="grid-field-duration">
      {{ $options.methods.formatValue(props.field, props.value) }}
    </div>
  </div>
</template>

<script>
import { DurationFieldType } from '@baserow/modules/database/fieldTypes'

export default {
  name: 'FunctionalGridViewFieldDuration',
  functional: true,
  methods: {
    formatValue(field, value) {
      return DurationFieldType.formatValue(field, value)
    },
  },
}
</script>
