<template functional>
  <div :class="[data.staticClass, data.class]" v-on="listeners">
    {{
      $options.methods.localDate(
        props.row[props.column.key],
        props.column.additionalProps.dateTimeFormat || 'L LT'
      )
    }}
  </div>
</template>

<script>
import moment from '@baserow/modules/core/moment'

export default {
  name: 'LocalDateField',
  functional: true,
  props: {
    row: {
      required: true,
      type: Object,
    },
    column: {
      required: true,
      type: Object,
    },
  },
  methods: {
    localDate(date, format) {
      if (date) {
        return moment.utc(date).local().format(format)
      } else {
        return ''
      }
    },
  },
}
</script>
