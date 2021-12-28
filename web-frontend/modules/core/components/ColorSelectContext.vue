<template>
  <Context ref="context" class="color-select-context">
    <div class="color-select-context__colors">
      <div
        v-for="(colorRow, rowIndex) in colors"
        :key="`color-row-${rowIndex}`"
        class="color-select-context__row"
      >
        <a
          v-for="(color, index) in colorRow"
          :key="`color-${index}`"
          class="color-select-context__color"
          :class="[
            `background-color--${color}`,
            color === active ? 'active' : '',
          ]"
          @click="select(color)"
        ></a>
      </div>
    </div>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import { colors as colorList } from '@baserow/modules/core/utils/colors'

const defaultColors = [
  colorList.slice(0, 5),
  colorList.slice(5, 10),
  colorList.slice(10, 15),
]

export default {
  name: 'ColorSelectContext',
  mixins: [context],
  props: {
    colors: {
      type: Array,
      default: () => defaultColors,
      required: false,
    },
  },
  data() {
    return {
      active: '',
    }
  },
  methods: {
    setActive(color) {
      this.active = color
    },
    select(color) {
      this.$emit('selected', color)
      this.hide()
    },
  },
}
</script>
