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
import dropdownItem from '@baserow/modules/core/mixins/dropdownItem'

export default {
  name: 'DropdownItem',
  mixins: [dropdownItem],
}
</script>
