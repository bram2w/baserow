<template functional>
  <div ref="cell" class="grid-view__cell">
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
import moment from 'moment'
import {
  getDateMomentFormat,
  getTimeMomentFormat,
} from '@baserow/modules/database/utils/date'

export default {
  name: 'FunctionalGridViewFieldDate',
  methods: {
    getDate(field, value) {
      if (value === null) {
        return ''
      }

      const existing = moment.utc(value || undefined)
      const dateFormat = getDateMomentFormat(field.date_format)
      return existing.format(dateFormat)
    },
    getTime(field, value) {
      if (value === null) {
        return ''
      }

      const existing = moment.utc(value || undefined)
      const timeFormat = getTimeMomentFormat(field.date_time_format)
      return existing.format(timeFormat)
    },
  },
}
</script>
