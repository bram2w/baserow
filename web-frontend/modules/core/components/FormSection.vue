<template>
  <div class="form-section">
    <h3 v-if="title" class="form-section__title">{{ title }}</h3>
    <slot />
  </div>
</template>

<script>
export default {
  name: 'FormSection',
  props: {
    title: {
      type: String,
      required: false,
      default: null,
    },
  },
}
</script>
