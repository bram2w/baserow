<template>
  <RadioGroup
    :model-value="value"
    :options="alignmentValues"
    type="button"
    @input="$emit('input', $event)"
  />
</template>

<script>
import { VERTICAL_ALIGNMENTS } from '@baserow/modules/builder/enums'

export default {
  name: 'VerticalAlignmentSelector',
  props: {
    value: {
      type: String,
      required: false,
      default: null,
    },
  },
  computed: {
    alignmentValues() {
      return [
        {
          title: this.$t('verticalAlignmentSelector.alignmentTop'),
          value: VERTICAL_ALIGNMENTS.TOP,
          icon: 'iconoir-align-top-box',
        },
        {
          title: this.$t('verticalAlignmentSelector.alignmentCenter'),
          value: VERTICAL_ALIGNMENTS.CENTER,
          icon: 'iconoir-center-align',
        },
        {
          title: this.$t('verticalAlignmentSelector.alignmentBottom'),
          value: VERTICAL_ALIGNMENTS.BOTTOM,
          icon: 'iconoir-align-bottom-box',
        },
      ]
    },
  },
}
</script>
