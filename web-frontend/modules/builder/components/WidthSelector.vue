<template>
  <RadioGroup
    :model-value="value"
    :options="options"
    type="button"
    @input="$emit('input', $event)"
  />
</template>

<script>
import { WIDTHS_NEW } from '@baserow/modules/builder/enums'

export default {
  name: 'WidthSelector',
  props: {
    value: {
      type: String,
      required: false,
      default: WIDTHS_NEW.AUTO,
    },
  },
  computed: {
    options() {
      return [
        { value: WIDTHS_NEW.AUTO, label: this.$t('widthSelector.widthAuto') },
        { value: WIDTHS_NEW.FULL, label: this.$t('widthSelector.widthFull') },
      ]
    },
  },
}
</script>
