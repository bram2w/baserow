<template>
  <span class="ab-tag" :style="{ ['--tag-background-color']: color }">
    <slot />
  </span>
</template>

<script>
export default {
  name: 'ABTag',
  props: {
    color: {
      type: String,
      required: false,
      default: '',
    },
  },
}
</script>
