<template>
  <ButtonIcon
    v-if="propertyModified()"
    v-tooltip="$t('resetButton.reset')"
    icon="iconoir-erase"
    @click="resetProperty()"
  />
</template>

<script>
import _ from 'lodash'

export default {
  inject: ['builder'],
  props: {
    theme: { type: Object, required: false, default: null },
    property: { type: String, required: true },
    value: { type: Object, required: true },
  },
  data() {
    return {}
  },
  methods: {
    propertyModified() {
      if (!this.theme) {
        return false
      }
      return !_.isEqual(this.value[this.property], this.theme[this.property])
    },
    resetProperty() {
      this.$emit('input', {
        ...this.value,
        [this.property]: this.theme[this.property],
      })
    },
  },
}
</script>
