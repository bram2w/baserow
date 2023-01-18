<template>
  <i v-tooltip="tooltip" class="help-icon fas" :class="iconClass"> </i>
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
      return this.isWarning ? 'fa-exclamation-circle' : 'fa-question-circle'
    },
  },
}
</script>
