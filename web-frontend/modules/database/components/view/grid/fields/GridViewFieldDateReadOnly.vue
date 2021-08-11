<template>
  <div ref="cell" class="grid-view__cell active">
    <div
      class="grid-field-date"
      :class="{ 'grid-field-date--has-time': field.date_include_time }"
    >
      <div ref="dateDisplay" class="grid-field-date__date">
        {{ getDate(field, value) }}
      </div>
      <div
        v-if="field.date_include_time"
        ref="timeDisplay"
        class="grid-field-date__time"
      >
        {{ getTime(field, value) }}
      </div>
    </div>
  </div>
</template>

<script>
import gridField from '@baserow/modules/database/mixins/gridField'
import readOnlyDateField from '@baserow/modules/database/mixins/readOnlyDateField'

export default {
  name: 'GridViewFieldDateReadOnly',
  mixins: [gridField, readOnlyDateField],
}
</script>
