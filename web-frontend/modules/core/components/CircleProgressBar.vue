<template>
  <svg
    :width="size"
    :height="size"
    :viewBox="`0 0 ${size} ${size}`"
    class="circle-progress-bar"
    :style="{
      '--size': `${size}px`,
      '--stroke-width': `${strokeWidth}px`,
      '--progress': value,
    }"
  >
    <circle class="circle-progress-bar__background"></circle>
    <circle class="circle-progress-bar__foreground"></circle>
  </svg>
</template>

<script>
export default {
  name: 'CircleProgressBar',
  props: {
    value: {
      type: Number,
      required: true,
    },
    size: {
      type: Number,
      required: false,
      default: 32,
    },
    strokeWidth: {
      type: Number,
      required: false,
      default: 4,
    },
  },
}
</script>
