<template>
  <i v-tooltip="tooltip" class="help-icon" :class="iconClass"> </i>
</template>

<script>
export default {
  name: 'HelpIcon',
  props: {
    tooltip: {
      type: String,
      required: false,
      default: null,
    },
    isWarning: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    iconClass() {
      return this.isWarning
        ? 'iconoir-warning-triangle'
        : 'iconoir-chat-bubble-question'
    },
  },
}
</script>
