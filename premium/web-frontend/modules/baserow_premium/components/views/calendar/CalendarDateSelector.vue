<template>
  <div class="calendar-date-selector">
    <a class="calendar-date-selector__prev" @click="selectPrevious">
      <i class="fas fa-chevron-left fa-1x"></i>
    </a>
    <a class="calendar-date-selector__next" @click="selectNext">
      <i class="fas fa-chevron-right fa-1x"></i>
    </a>
    <button class="button button--large button--ghost" @click="selectCurrent">
      {{ $t('calendarDateSelector.today') }}
    </button>
  </div>
</template>

<script>
import moment from '@baserow/modules/core/moment'

export default {
  name: 'CalendarDateSelector',
  props: {
    currentDate: {
      type: String,
      required: true,
    },
    selectedDate: {
      type: Object,
      required: true,
    },
  },
  methods: {
    selectPrevious() {
      const newSelectedDate = moment(this.selectedDate).subtract(1, 'month')
      this.$emit('date-selected', newSelectedDate)
    },
    selectCurrent() {
      const newSelectedDate = moment(this.currentDate)
      this.$emit('date-selected', newSelectedDate)
    },
    selectNext() {
      const newSelectedDate = moment(this.selectedDate).add(1, 'month')
      this.$emit('date-selected', newSelectedDate)
    },
  },
}
</script>
