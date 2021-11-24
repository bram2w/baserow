<template functional>
  <div ref="cell" class="grid-view__cell" :class="data.staticClass || ''">
    <div
      class="grid-field-date"
      :class="{ 'grid-field-date--has-time': props.field.date_include_time }"
    >
      <div ref="dateDisplay" class="grid-field-date__date">
        {{ $options.methods.getDate(props.field, props.value) }}
      </div>
      <div
        v-if="props.field.date_include_time"
        ref="timeDisplay"
        class="grid-field-date__time"
      >
        {{ $options.methods.getTime(props.field, props.value) }}
      </div>
    </div>
  </div>
</template>

<script>
import readOnlyDateField from '@baserow/modules/database/mixins/readOnlyDateField'

export default {
  name: 'FunctionalGridViewFieldDate',
  mixins: [readOnlyDateField],
}
</script>
