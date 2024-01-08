<template>
  <div class="badge" :class="classes">
    <i v-if="indicator" class="badge__indicator"></i>
    <span class="badge__label"><slot /></span>
  </div>
</template>

<script>
export default {
  name: 'Badge',
  props: {
    /**
     * The color scheme of the badge
     * Possible values are: `cyan` | `green` | `yellow` | `red` | `magenta` | `purple` | `neutral`
     */
    color: {
      type: String,
      required: false,
      default: 'neutral',
      validator: function (value) {
        return [
          'cyan',
          'green',
          'yellow',
          'red',
          'magenta',
          'purple',
          'neutral',
        ].includes(value)
      },
    },
    /**
     * Display a small indicator dot on the badge if true
     */
    indicator: {
      type: Boolean,
      required: false,
      default: false,
    },
    /**
     * Display a more rounded badge if true
     */
    rounded: {
      type: Boolean,
      required: false,
      default: false,
    },
    /**
     * The size of the badge
     * Possible values are: `regular` | `small` | `large`
     */
    size: {
      type: String,
      required: false,
      default: 'regular',
      validator: function (value) {
        return ['regular', 'small', 'large'].includes(value)
      },
    },
    /**
     * Make the text of the badge bold if true
     */
    bold: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    classes() {
      const classObj = {
        [`badge--${this.color}`]: this.color,
        [`badge--${this.size}`]: this.size,
        [`badge--rounded`]: this.rounded,
        [`badge--bold`]: this.bold,
      }
      return classObj
    },
  },
}
</script>
