<!-- eslint-disable vue/no-v-html -->
<template>
  <div
    class="template__illustration"
    :class="`template__illustration--${color}`"
  >
    <div
      class="template__illustration-image"
      v-html="
        require(`@baserow/modules/core/assets/images/template_illustration_${type}_${color}.svg?raw`)
      "
    />
  </div>
</template>

<script>
export default {
  props: {
    color: {
      type: String,
      default: 'green',
      validator: (value) =>
        ['red', 'green', 'blue', 'magenta', 'purple', 'yellow'].includes(value),
    },
    type: {
      type: String,
      default: 'table',
      validator: (value) =>
        ['calendar', 'table', 'kanban', 'gallery', 'form'].includes(value),
    },
  },
}
</script>
