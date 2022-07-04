<template>
  <div class="progress-bar">
    <div
      class="progress-bar__inner"
      :style="{
        width: `${value}%`,
        'transition-duration': [100, 0].includes(value) ? '0s' : '1s',
      }"
    ></div>
    <span class="progress-bar__status-text">
      <template v-if="showValue">{{ `${displayValue}%` }}</template>
      {{ status }}
    </span>
  </div>
</template>

<script>
export default {
  name: 'ProgressBar',
  props: {
    value: {
      type: Number,
      required: true,
    },
    status: {
      type: String,
      required: false,
      default: '',
    },
    showValue: {
      type: Boolean,
      required: false,
      default: true,
    },
  },
  computed: {
    displayValue() {
      return Math.round(this.value)
    },
  },
}
</script>
