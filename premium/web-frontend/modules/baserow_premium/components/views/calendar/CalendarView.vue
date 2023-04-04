<template>
  <CalendarMonth
    :fields="fields"
    :store-prefix="storePrefix"
    :loading="loading"
  ></CalendarMonth>
</template>
<script>
import CalendarMonth from '@baserow_premium/components/views/calendar/CalendarMonth'

export default {
  name: 'CalendarView',
  components: {
    CalendarMonth,
  },
  props: {
    database: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
    loading: {
      type: Boolean,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
  },
}
</script>
