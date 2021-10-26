<template>
  <Context ref="context" class="color-select-context">
    <div class="color-select-context__colors">
      <a
        v-for="(color, index) in colors"
        :key="color + '-' + index"
        class="color-select-context__color"
        :class="
          'background-color--' +
          color +
          ' ' +
          (color === active ? 'active' : '')
        "
        @click="select(color)"
      ></a>
    </div>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import { colors } from '@baserow/modules/core/utils/colors'

export default {
  name: 'ColorSelectContext',
  mixins: [context],
  data() {
    return {
      active: '',
    }
  },
  computed: {
    colors() {
      return colors
    },
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
