<template>
  <div class="grid-view-cell" :class="{ active: selected }">
    <div class="grid-field-boolean">
      <div
        class="grid-field-checkbox"
        :class="{ active: value }"
        @click="toggle(value)"
      >
        <i class="fas fa-check check"></i>
      </div>
    </div>
  </div>
</template>

<script>
import gridField from '@baserow/modules/database/mixins/gridField'

export default {
  mixins: [gridField],
  methods: {
    toggle(value) {
      if (!this.selected) {
        return
      }
      const oldValue = !!value
      const newValue = !value
      this.$emit('update', newValue, oldValue)
    }
  }
}
</script>
