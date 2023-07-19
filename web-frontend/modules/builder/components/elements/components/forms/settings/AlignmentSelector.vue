<template>
  <div>
    <label class="control__label">
      {{ $t('alignmentSelector.alignment') }}
    </label>
    <div class="control__elements">
      <RadioButton
        v-for="alignment in alignments"
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
import { ALIGNMENTS } from '@baserow/modules/builder/enums'

export default {
  name: 'AlignmentSelector',
  props: {
    value: {
      type: String,
      required: false,
      default: ALIGNMENTS.LEFT.value,
    },
  },
  data() {
    return {
      selected: this.value,
    }
  },
  computed: {
    alignments() {
      return Object.values(ALIGNMENTS)
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
