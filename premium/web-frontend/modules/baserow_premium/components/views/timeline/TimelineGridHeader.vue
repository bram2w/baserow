<template>
  <div class="timeline-grid-header" :style="{ width: `${gridWidth}px` }">
    <template v-for="(slot, index) in columnsBuffer">
      <div
        v-show="slot.item !== undefined"
        :key="`h-${index}`"
        :style="{
          transform: `translateX(${slot.position.left || 0}px)`,
          width: `${columnWidth}px`,
        }"
        class="timeline-grid-header__column"
      >
        <div>{{ formatDate(slot.item.date) }}</div>
      </div>
    </template>
  </div>
</template>

<script>
import moment from '@baserow/modules/core/moment'

export default {
  name: 'TimelineGridHeader',
  props: {
    columnsBuffer: {
      type: Array,
      required: true,
    },
    columnWidth: {
      type: Number,
      required: true,
    },
    columnCount: {
      type: Number,
      required: true,
    },
    dateFormat: {
      type: String,
      default: 'D',
    },
  },
  computed: {
    gridWidth() {
      return this.columnCount * this.columnWidth
    },
  },
  methods: {
    formatDate(date) {
      return moment(date).format(this.dateFormat)
    },
  },
}
</script>
