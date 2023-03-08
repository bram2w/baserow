<template functional>
  <div class="card-text">
    {{ $options.methods.getDate(props.field, props.value) }}
    <template v-if="props.field.date_include_time">{{
      $options.methods.getTime(props.field, props.value)
    }}</template>
    <span v-if="props.field.date_show_tzinfo" class="color--tzinfo">
      {{ $options.methods.getCellTimezoneAbbr(props.field, props.value) }}
    </span>
  </div>
</template>

<script>
import readOnlyDateField from '@baserow/modules/database/mixins/readOnlyDateField'

export default {
  height: 16,
  name: 'RowCardFieldDate',
  mixins: [readOnlyDateField],
}
</script>
