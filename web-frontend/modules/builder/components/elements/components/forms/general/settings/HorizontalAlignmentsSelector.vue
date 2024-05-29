<template>
  <div>
    <label class="control__label">
      {{ $t('horizontalAlignmentSelector.alignment') }}
    </label>
    <div class="control__elements">
      <RadioGroup
        v-model="selected"
        :options="alignmentValues"
        type="button"
        @input="$emit('input', $event)"
      >
      </RadioGroup>
    </div>
  </div>
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
    alignments: {
      type: Object,
      required: false,
      default: () => HORIZONTAL_ALIGNMENTS,
    },
  },
  data() {
    return {
      selected: this.value,
    }
  },
  computed: {
    alignmentValues() {
      const values = Object.values(this.alignments)
      return values.map((value) => {
        return {
          icon: value.icon,
          value: value.value,
          title: this.$t(value.name),
        }
      })
    },
  },
  watch: {
    value: {
      handler(value) {
        this.selected = value
      },
      immediate: true,
    },
  },
}
</script>
