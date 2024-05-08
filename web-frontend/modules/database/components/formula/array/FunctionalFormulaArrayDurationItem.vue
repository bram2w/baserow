<template functional>
  <div v-if="props.value !== null" class="array-field__item">
    <span>
      {{ $options.methods.formatValue(props.field, props.value) }}
    </span>
  </div>
</template>

<script>
import durationField from '@baserow/modules/database/mixins/durationField'
export default {
  name: 'FunctionalFormulaArrayDurationItem',
  mixins: [durationField],
}
</script>
