<template>
  <component
    :is="type === 'link' || href ? 'a' : 'button'"
    class="button"
    :class="classes"
    :disable="disabled"
    :active="active"
    v-bind.prop="customBind"
    v-on="$listeners"
  >
    <i
      v-if="prependIcon"
      class="button__icon fas"
      :class="`fa-${prependIcon}`"
    />
    <slot />
    <i
      v-if="appendIcon || icon"
      class="button__icon fas"
      :class="appendIcon ? `fa-${appendIcon}` : `fa-${icon}`"
    />
  </component>
</template>

<script>
export default {
  props: {
    type: {
      // link - button
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
    color: {
      //  primary - success - warning - error - ghost - light
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
      const classObj = {
        [`button--${this.size}`]: this.size,
        [`button--${this.color}`]: this.color,
        'button--primary': !this.color,
        'button--full-width': this.fullWidth,
        'button--icon': this.prependIcon || this.appendIcon || this.icon,
        'button--loading': this.loading,
        disabled: this.disabled,
        active: this.active,
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
