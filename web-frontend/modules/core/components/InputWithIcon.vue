<template>
  <div class="input__with-icon" :class="iconPositionClass">
    <input
      type="text"
      class="input"
      :placeholder="placeholder"
      @input="$emit('input', $event.target.value)"
    />
    <i class="fas" :class="[iconSizeClass, iconClass]"></i>
  </div>
</template>

<script>
const ICON_POSITION_CSS_MAP = {
  left: 'input__with-icon--left',
  right: null,
}

export default {
  name: 'InputWithIcon',
  inheritAttrs: false,
  props: {
    value: {
      type: String,
      required: false,
      default: '',
    },
    icon: {
      type: String,
      required: true,
    },
    iconSize: {
      type: String,
      required: false,
      default: null,
    },
    iconPosition: {
      type: String,
      required: false,
      default: 'right',
      validator: (value) => {
        return Object.keys(ICON_POSITION_CSS_MAP).includes(value)
      },
    },
    placeholder: {
      type: String,
      required: false,
      default: null,
    },
  },
  computed: {
    iconClass() {
      return `fa-${this.icon}`
    },
    iconSizeClass() {
      return this.iconSize ? `fa-${this.iconSize}` : null
    },
    iconPositionClass() {
      return ICON_POSITION_CSS_MAP[this.iconPosition]
    },
  },
}
</script>
