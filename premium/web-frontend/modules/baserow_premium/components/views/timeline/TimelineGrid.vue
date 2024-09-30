<template>
  <div
    class="timeline-grid"
    :style="{
      height: `${gridHeight}px`,
      width: `${gridWidth}px`,
    }"
  >
    <template v-for="(slot, index) in columnsBuffer">
      <div
        v-show="slot.item !== undefined"
        :key="`c-${index}`"
        :style="{
          transform: `translateX(${slot.position.left}px)`,
          width: `${columnWidth}px`,
          height: `${gridHeight}px`,
        }"
        class="timeline-grid__column"
        :class="{ 'timeline-grid__column--weekend': slot.item?.isWeekend }"
      ></div>
    </template>

    <div
      v-if="offsetNow"
      :style="{
        transform: `translateX(${offsetNow}px)`,
        height: `${gridHeight}px`,
      }"
      class="timeline-grid__now-cursor"
    ></div>
  </div>
</template>

<script>
import moment from '@baserow/modules/core/moment'

export default {
  name: 'TimelineGrid',
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
    minHeight: {
      type: Number,
      required: true,
    },
  },
  computed: {
    gridHeight() {
      // TODO: Use the rowCount to calculate the height of the grid.
      return this.minHeight
    },
    gridWidth() {
      return this.columnCount * this.columnWidth
    },
    offsetNow() {
      const firstDate = this.columnsBuffer[0]?.item?.date
      if (!firstDate) {
        return null
      }
      const lastDate =
        this.columnsBuffer[this.columnsBuffer.length - 1]?.item?.date
      const now = moment().utcOffset(firstDate.utcOffset())
      if (now.isBefore(firstDate) || now.isAfter(lastDate)) {
        return null
      }
      const firstDateOffset = this.columnsBuffer[0].position.left
      return (
        firstDateOffset + now.diff(firstDate, 'days', true) * this.columnWidth
      )
    },
  },
}
</script>
