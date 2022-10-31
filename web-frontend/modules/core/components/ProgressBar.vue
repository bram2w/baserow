<template>
  <div class="progress-bar">
    <div
      class="progress-bar__inner"
      :class="
        showOverflow && overflowing ? 'progress-bar__inner--overflow' : ''
      "
      :style="{
        width: `${constrainedValue}%`,
        'transition-duration': [100, 0].includes(constrainedValue)
          ? '0s'
          : '1s',
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
    showOverflow: {
      required: false,
      type: Boolean,
      default: false,
    },
  },
  computed: {
    constrainedValue() {
      return this.showOverflow ? Math.min(this.value, 100) : this.value
    },
    displayValue() {
      return Math.round(this.value)
    },
    overflowing() {
      return this.value > 100
    },
  },
}
</script>
