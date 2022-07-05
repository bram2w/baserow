<template>
  <div
    class="alert"
    :class="{
      'alert--simple': simple,
      [`alert--${type}`]: type,
      'alert--has-icon': icon,
      'alert--with-shadow': shadow,
    }"
  >
    <div v-if="icon" class="alert__icon">
      <i class="fas" :class="`fa-${icon}`" />
    </div>
    <div class="alert__title">{{ title }}</div>
    <p class="alert__content"><slot /></p>
  </div>
</template>

<script>
export default {
  props: {
    type: {
      required: false,
      type: String,
      default: '',
    },
    simple: {
      required: false,
      type: Boolean,
      default: false,
    },
    shadow: {
      required: false,
      type: Boolean,
      default: false,
    },
    title: {
      required: true,
      type: String,
    },
    icon: {
      required: false,
      type: String,
      default: '',
    },
  },
}
</script>
