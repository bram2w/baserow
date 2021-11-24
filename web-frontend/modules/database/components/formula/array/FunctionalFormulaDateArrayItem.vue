<template functional>
  <div class="array-field__date">
    <div>
      {{ $options.methods.getDate(props.field, props.value) }}
    </div>
    <div v-if="props.field.date_include_time" class="array-field__time">
      {{ $options.methods.getTime(props.field, props.value) }}
    </div>
  </div>
</template>

<script>
import readOnlyDateField from '@baserow/modules/database/mixins/readOnlyDateField'
export default {
  name: 'FunctionalFormulaDateArrayItem',
  mixins: [readOnlyDateField],
}
</script>
