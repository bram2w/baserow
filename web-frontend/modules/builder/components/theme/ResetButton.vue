<template>
  <ButtonIcon
    v-if="propertyModified()"
    v-tooltip="$t('resetButton.reset')"
    tooltip-position="bottom-left"
    icon="iconoir-erase"
    @click="resetProperty()"
  />
</template>

<script>
import _ from 'lodash'

export default {
  inject: ['builder'],
  props: {
    value: { required: true, validator: (v) => true },
    defaultValue: {
      required: false,
      validator: (v) => true,
      default: undefined,
    },
  },
  data() {
    return {}
  },
  methods: {
    propertyModified() {
      return (
        this.defaultValue !== undefined &&
        !_.isEqual(this.value, this.defaultValue)
      )
    },
    resetProperty() {
      this.$emit('input', this.defaultValue)
    },
  },
}
</script>
