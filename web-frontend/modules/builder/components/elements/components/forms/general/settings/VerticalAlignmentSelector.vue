<template>
  <div>
    <label class="control__label">
      {{ $t('verticalAlignmentSelector.alignment') }}
    </label>
    <Dropdown
      class="control__elements"
      :show-search="false"
      :value="value"
      @input="$emit('input', $event)"
    >
      <DropdownItem
        v-for="alignment in alignmentValues"
        :key="alignment.value"
        :name="$t(alignment.name)"
        :value="alignment.value"
      >
        {{ $t(alignment.name) }}
      </DropdownItem>
    </Dropdown>
  </div>
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
    alignments: {
      type: Object,
      required: false,
      default: () => VERTICAL_ALIGNMENTS,
    },
  },
  computed: {
    alignmentValues() {
      return Object.values(this.alignments)
    },
  },
}
</script>
