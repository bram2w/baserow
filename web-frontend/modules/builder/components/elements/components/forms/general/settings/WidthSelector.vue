<template>
  <div>
    <label class="control__label">
      {{ $t('widthSelector.width') }}
    </label>
    <div class="control__elements">
      <RadioButton
        v-for="width in widths"
        :key="width.value"
        :value="width.value"
        :model-value="value"
        @input="$emit('input', $event)"
      >
        {{ $t(width.name) }}
      </RadioButton>
    </div>
  </div>
</template>

<script>
import { WIDTHS } from '@baserow/modules/builder/enums'

export default {
  name: 'WidthSelector',
  props: {
    value: {
      type: String,
      required: false,
      default: WIDTHS.AUTO.value,
    },
    widths: {
      type: Array,
      required: false,
      default: () => Object.values(WIDTHS),
    },
  },
}
</script>
