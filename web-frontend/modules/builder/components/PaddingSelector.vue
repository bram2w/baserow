<template>
  <div class="padding-selector">
    <FormInput
      small
      :value="value.horizontal"
      type="number"
      remove-number-input-controls
      :to-value="(val) => parseInt(val)"
      class="padding-selector__input"
      icon-right="iconoir-horizontal-split"
      @input="$emit('input', { horizontal: $event, vertical: value.vertical })"
      @blur="$emit('blur')"
    />
    <FormInput
      small
      :value="value.vertical"
      type="number"
      remove-number-input-controls
      :to-value="(val) => parseInt(val)"
      class="padding-selector__input"
      icon-right="iconoir-vertical-split"
      @input="
        $emit('input', { horizontal: value.horizontal, vertical: $event })
      "
      @blur="$emit('blur')"
    />
  </div>
</template>

<script>
export default {
  name: 'PaddingSelector',
  props: {
    value: {
      type: Object,
      required: true,
    },
  },
}
</script>
