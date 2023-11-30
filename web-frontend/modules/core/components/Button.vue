<template>
  <component
    :is="tag === 'a' || href ? 'a' : 'button'"
    class="button"
    :class="classes"
    :disable="disabled"
    :active="active"
    v-bind.prop="customBind"
    v-on="$listeners"
  >
    <i v-if="prependIcon" class="button__icon" :class="prependIcon" />
    <slot></slot>
    <i
      v-if="appendIcon || icon"
      class="button__icon"
      :class="appendIcon ? appendIcon : icon"
    />
  </component>
</template>

<script>
export default {
  props: {
    tag: {
      // a - button
      required: false,
      type: String,
      default: 'button',
    },
    size: {
      // tiny - normal - large
      required: false,
      type: String,
      default: '',
    },
    type: {
      //  primary - success - warning - error - ghost - light - link
      required: false,
      type: String,
      default: '',
    },
    prependIcon: {
      required: false,
      type: String,
      default: '',
    },
    appendIcon: {
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
    disabled: {
      required: false,
      type: Boolean,
      default: false,
    },
    fullWidth: {
      required: false,
      type: Boolean,
      default: false,
    },
    active: {
      required: false,
      type: Boolean,
      default: false,
    },
    overflow: {
      required: false,
      type: Boolean,
      default: false,
    },
    href: {
      required: false,
      type: String,
      default: '',
    },
    target: {
      required: false,
      type: String,
      default: 'self',
    },
  },
  computed: {
    classes() {
      const hasIcon = this.prependIcon || this.appendIcon || this.icon
      const classObj = {
        [`button--${this.size}`]: this.size,
        [`button--${this.type}`]: this.type,
        'button--primary': !this.type,
        'button--full-width': this.fullWidth,
        'button--icon-only': hasIcon && !this.$slots.default,
        'button--loading': this.loading,
        disabled: this.disabled,
        active: this.active && !this.loading && !this.disabled,
        'button--overflow': this.overflow,
      }
      return classObj
    },
    customBind() {
      const attr = {}
      if (this.href) {
        attr.href = this.href
      }
      if (this.target) {
        attr.target = `_${this.target}`
      }
      return attr
    },
  },
}
</script>
