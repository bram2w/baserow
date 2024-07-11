<template>
  <RadioGroup
    :model-value="value"
    :options="alignmentValues"
    type="button"
    @input="$emit('input', $event)"
  />
</template>

<script>
import { HORIZONTAL_ALIGNMENTS } from '@baserow/modules/builder/enums'

export default {
  name: 'HorizontalAlignmentsSelector',
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
          title: this.$t('horizontalAlignmentSelector.alignmentLeft'),
          value: HORIZONTAL_ALIGNMENTS.LEFT,
          icon: 'iconoir-align-left',
        },
        {
          title: this.$t('horizontalAlignmentSelector.alignmentCenter'),
          value: HORIZONTAL_ALIGNMENTS.CENTER,
          icon: 'iconoir-align-center',
        },
        {
          title: this.$t('horizontalAlignmentSelector.alignmentRight'),
          value: HORIZONTAL_ALIGNMENTS.RIGHT,
          icon: 'iconoir-align-right',
        },
      ]
    },
  },
}
</script>
