<template functional>
  <div v-if="props.value !== null" class="array-field__item">
    <div class="array-field__ellipsis">
      {{ $options.methods.formatValue(props.field, props.value) }}
    </div>
  </div>
</template>

<script>
import durationField from '@baserow/modules/database/mixins/durationField'
export default {
  name: 'FunctionalFormulaArrayDurationItem',
  mixins: [durationField],
}
</script>
