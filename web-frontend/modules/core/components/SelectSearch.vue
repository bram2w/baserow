<template>
  <div class="select__search">
    <i class="select__search-icon iconoir-search"></i>
    <input
      :value="value"
      type="text"
      class="select__search-input"
      v-bind="$attrs"
      @input="$emit('input', $event.target.value)"
    />
  </div>
</template>

<script>
export default {
  name: 'SelectSearch',
  props: {
    value: {
      type: String,
      required: false,
      default: null,
    },
  },
}
</script>
