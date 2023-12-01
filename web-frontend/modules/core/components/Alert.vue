<template>
  <div class="alert" :class="classes">
    <i v-if="loading" class="alert__loading"></i>
    <i v-else class="alert__icon" :class="iconClass"></i>

    <div class="alert__content">
      <div v-if="hasTitleSlot" class="alert__title">
        <slot name="title" />
      </div>
      <div v-if="hasDefaultSlot" class="alert__message"><slot /></div>

      <div v-if="hasActionsSlot" class="alert__actions">
        <slot name="actions" />
      </div>
    </div>

    <button v-if="closeButton" class="alert__close" @click="close">
      <i class="iconoir-cancel"></i>
    </button>
  </div>
</template>

<script>
export default {
  props: {
    /**
     * The type of alert to display
     */
    type: {
      required: false,
      type: String,
      default: 'info-primary',
      validator: function (value) {
        return [
          'info-neutral',
          'info-primary',
          'warning',
          'error',
          'success',
        ].includes(value)
      },
    },
    /**
     * The position of the alert. If not set it will be display in the flow.
     */
    position: {
      required: false,
      type: String,
      default: null,
      validator: function (value) {
        return ['top', 'bottom'].includes(value)
      },
    },
    /**
     * Whether to display a loading spinner or not.
     */
    loading: {
      required: false,
      type: Boolean,
      default: false,
    },
    /**
     * Whether to display a close button or not.
     */
    closeButton: {
      required: false,
      type: Boolean,
      default: false,
    },
  },
  computed: {
    hasDefaultSlot() {
      return !!this.$slots.default
    },
    hasTitleSlot() {
      return !!this.$slots.title
    },
    hasActionsSlot() {
      return !!this.$slots.actions
    },
    classes() {
      const classObj = {
        [`alert--${this.type}`]: this.type,
        [`alert--${this.position}`]: this.position,
      }
      return classObj
    },
    isWarningAlert() {
      return this.type === 'warning'
    },
    isErrorAlert() {
      return this.type === 'error'
    },
    isInfoAlert() {
      return this.type === 'info-neutral' || this.type === 'info-primary'
    },
    isSuccessAlert() {
      return this.type === 'success'
    },
    iconClass() {
      const classObj = {
        'iconoir-warning-triangle': this.isWarningAlert,
        'iconoir-info-empty': this.isInfoAlert,
        'iconoir-check-circle': this.isSuccessAlert,
        'iconoir-warning-circle': this.isErrorAlert,
      }
      return classObj
    },
  },
  methods: {
    close() {
      this.$emit('close')
    },
  },
}
</script>
