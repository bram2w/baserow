<template>
  <div>
    <label class="control__label">
      {{ $t('horizontalAlignmentSelector.alignment') }}
    </label>
    <div class="control__elements">
      <RadioButton
        v-for="alignment in alignmentValues"
        :key="alignment.value"
        v-model="selected"
        :value="alignment.value"
        :icon="alignment.icon"
        :title="$t(alignment.name)"
        @input="$emit('input', $event)"
      />
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
      return Object.values(this.alignments)
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
