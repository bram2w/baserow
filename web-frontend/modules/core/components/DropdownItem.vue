<template>
  <li
    class="select__item"
    :class="{
      hidden: !isVisible(query),
      active: isActive(value),
      disabled: disabled,
      hover: isHovering(value),
    }"
  >
    <a
      class="select__item-link"
      @click="select(value, disabled)"
      @mousemove="hover(value, disabled)"
    >
      <i
        v-if="icon"
        class="select__item-icon fas fa-fw"
        :class="'fa-' + icon"
      ></i>
      {{ name }}
    </a>
  </li>
</template>

<script>
export default {
  name: 'DropdownItem',
  props: {
    value: {
      type: [String, Number, Boolean, Object],
      required: true,
    },
    name: {
      type: String,
      required: true,
    },
    icon: {
      type: String,
      required: false,
      default: null,
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      query: '',
    }
  },
  methods: {
    select(value, disabled) {
      if (!disabled) {
        this.$parent.select(value)
      }
    },
    hover(value, disabled) {
      if (!disabled && this.$parent.hover !== value) {
        this.$parent.hover = value
      }
    },
    search(query) {
      this.query = query
    },
    isVisible(query) {
      const regex = new RegExp('(' + query + ')', 'i')
      return this.name.match(regex)
    },
    isActive(value) {
      return this.$parent.value === value
    },
    isHovering(value) {
      return this.$parent.hover === value
    },
  },
}
</script>
