<template>
  <li
    class="field-single-select__dropdown-item"
    :class="{
      hidden: !isVisible(query),
      active: isActive(value),
      disabled: disabled,
      hover: isHovering(value),
    }"
  >
    <a
      class="field-single-select__dropdown-link"
      @click="select(value, disabled)"
      @mousemove="hover(value, disabled)"
    >
      <div
        class="field-single-select__dropdown-option"
        :class="'background-color--' + color"
      >
        {{ name }}
      </div>
    </a>
  </li>
</template>

<script>
import dropdownItem from '@baserow/modules/core/mixins/dropdownItem'

export default {
  name: 'FieldSingleSelectDropdownItem',
  mixins: [dropdownItem],
  props: {
    color: {
      type: String,
      required: false,
      default: '',
    },
  },
}
</script>
