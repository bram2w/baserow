<template>
  <a
    :class="{
      'ab-link': variant !== 'button',
      'ab-button ab-button--medium': variant === 'button',
      'ab-button--full-width': variant === 'button' && fullWidth === true,
    }"
    v-on="$listeners"
  >
    <slot></slot>
  </a>
</template>

<script>
/**
 * @typedef ABLink
 */

export default {
  name: 'ABLink',
  props: {
    /**
     * @type {string} - The variant of the link. Can be `link` (default) or `button`.
     */
    variant: {
      type: String,
      required: false,
      default: 'link',
      validator(value) {
        return ['link', 'button'].includes(value)
      },
    },
    /**
     * @type {string} - Wheter the button should be full width.
     */
    fullWidth: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
}
</script>
