<template>
  <div
    class="alert"
    :class="{
      'alert--simple': simple,
      [`alert--${type}`]: type,
      'alert--has-icon': icon || loading,
      'alert--with-shadow': shadow,
      'alert--minimal': minimal,
    }"
  >
    <a v-if="closeButton" class="alert__close" @click="$emit('close')">
      <i class="fas fa-times"></i>
    </a>

    <div v-if="loading" class="alert__icon">
      <div class="loading alert__icon-loading"></div>
    </div>

    <div v-if="icon && !loading" class="alert__icon">
      <i v-if="icon" class="fas" :class="`fa-${icon}`" />
    </div>

    <div v-if="!minimal" class="alert__title">{{ title }}</div>

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
      required: false,
      type: String,
      default: '',
    },
    icon: {
      required: false,
      type: String,
      default: '',
    },
    loading: {
      required: false,
      type: Boolean,
      default: false,
    },
    closeButton: {
      required: false,
      type: Boolean,
      default: false,
    },
    minimal: {
      required: false,
      type: Boolean,
      default: false,
    },
  },
}
</script>
