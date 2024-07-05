<template>
  <FormGroup v-if="!labelAfter" small-label required :label="label">
    <ColorInput
      :value="value"
      :color-variables="colorVariables"
      @input="$emit('input', $event)"
    />
    <template #after-input>
      <slot name="after-input"></slot>
    </template>
  </FormGroup>
  <div v-else class="control">
    <div class="control__elements">
      <div class="color-input-group--label-after">
        <ColorInput
          :value="value"
          :color-variables="colorVariables"
          :horizontal="horizontal"
          @input="$emit('input', $event)"
        />
        <div class="color-input-group__label-after">
          {{ label }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import ColorInput from '@baserow/modules/core/components/ColorInput'

export default {
  name: 'ColorInputGroup',
  components: { ColorInput },
  props: {
    value: {
      type: String,
      required: false,
      default: 'primary',
    },
    label: {
      type: String,
      required: true,
    },
    labelAfter: {
      type: Boolean,
      required: false,
      default: false,
    },
    colorVariables: {
      type: Array,
      required: false,
      default: () => [],
    },
    horizontal: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
}
</script>
