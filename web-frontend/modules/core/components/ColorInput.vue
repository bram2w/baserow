<template>
  <div>
    <ColorPickerContext
      ref="colorPicker"
      :value="value"
      :variables="colorVariables"
      @input="$emit('input', $event)"
    />
    <a
      ref="opener"
      class="color-input__preview"
      :style="{
        'background-color': resolveColor(value, colorVariables),
      }"
      @click="$refs.colorPicker.toggle($refs.opener)"
    />
  </div>
</template>

<script>
import ColorPickerContext from '@baserow/modules/core/components/ColorPickerContext'
import { resolveColor } from '@baserow/modules/core/utils/colors'

export default {
  name: 'ColorInput',
  components: { ColorPickerContext },
  props: {
    value: {
      type: String,
      required: false,
      default: 'primary',
    },
    colorVariables: {
      type: Array,
      required: false,
      default: () => [],
    },
  },
  methods: { resolveColor },
}
</script>
