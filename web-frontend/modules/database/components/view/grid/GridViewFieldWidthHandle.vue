<template>
  <div :class="{ dragging: dragging }" @mousedown.stop="start($event)"></div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'GridViewFieldWidthHandle',
  props: {
    grid: {
      type: Object,
      required: true,
    },
    field: {
      type: Object,
      required: true,
    },
    width: {
      type: Number,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      dragging: false,
      mouseStart: 0,
      startWidth: 0,
    }
  },
  methods: {
    start(event) {
      event.preventDefault()
      this.dragging = true
      this.mouseStart = event.clientX
      this.startWidth = parseFloat(this.width)

      this.$el.moveEvent = (event) => this.move(event)
      this.$el.upEvent = (event) => this.up(event)

      window.addEventListener('mousemove', this.$el.moveEvent)
      window.addEventListener('mouseup', this.$el.upEvent)
      document.body.classList.add('resizing-horizontal')
    },
    move(event) {
      event.preventDefault()
      const difference = event.clientX - this.mouseStart
      const newWidth = Math.max(this.startWidth + difference, 100)

      this.$store.dispatch(
        this.storePrefix + 'view/grid/setFieldOptionsOfField',
        {
          field: this.field,
          values: { width: newWidth },
        }
      )
    },
    async up(event) {
      event.preventDefault()
      this.dragging = false
      const difference = event.clientX - this.mouseStart
      const newWidth = Math.max(this.startWidth + difference, 100)
      window.removeEventListener('mousemove', this.$el.moveEvent)
      window.removeEventListener('mouseup', this.$el.upEvent)
      document.body.classList.remove('resizing-horizontal')

      if (newWidth === this.startWidth) {
        return
      }

      try {
        await this.$store.dispatch(
          this.storePrefix + 'view/grid/updateFieldOptionsOfField',
          {
            gridId: this.grid.id,
            field: this.field,
            values: { width: newWidth },
            oldValues: { width: this.startWidth },
          }
        )
      } catch (error) {
        notifyIf(error, 'field')
      }
    },
  },
}
</script>
