<template functional>
  <div :class="[data.staticClass, data.class]" v-on="listeners">
    {{ $options.methods.localDate(props.row[props.column.key]) }}
  </div>
</template>

<script>
import moment from 'moment'
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
    localDate(date) {
      if (date) {
        return moment.utc(date).local().format('L LT')
      } else {
        return ''
      }
    },
  },
}
</script>
