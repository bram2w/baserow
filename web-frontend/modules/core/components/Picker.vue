<template>
  <div class="dropdown">
    <a
      ref="pickerLink"
      class="dropdown__selected"
      @click="$refs.pickerContext.toggle($refs.pickerLink, 'bottom', 'left', 2)"
    >
      <i class="dropdown__selected-icon" :class="icon" />
      <span class="dropdown__selected-text">{{ name }}</span>
      <i class="dropdown__toggle-icon iconoir-nav-arrow-down"></i>
    </a>
    <Context
      ref="pickerContext"
      class="picker__context"
      :overflow-scroll="true"
      :max-height-if-outside-viewport="true"
    >
      <slot :hide-picker="hide" />
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
