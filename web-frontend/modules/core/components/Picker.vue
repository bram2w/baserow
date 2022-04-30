<template>
  <div class="dropdown">
    <a
      ref="pickerLink"
      class="dropdown__selected"
      @click="$refs.pickerContext.toggle($refs.pickerLink, 'bottom', 'left', 2)"
    >
      <i class="dropdown__selected-icon fas" :class="'fa-' + icon" />
      {{ name }}
      <i class="dropdown__toggle-icon fas fa-caret-down"></i>
    </a>
    <Context ref="pickerContext" class="picker__context">
      <slot :hidePicker="hide" />
    </Context>
  </div>
</template>

<script>
export default {
  name: 'Picker',
  props: {
    name: {
      type: String,
      required: true,
    },
    icon: {
      type: String,
      required: false,
      default: '',
    },
  },
  methods: {
    hide() {
      this.$refs.pickerContext.hide()
    },
  },
}
</script>
