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
      <div class="select__item-name">
        <slot>
          <i
            v-if="icon"
            v-tooltip="iconTooltip"
            class="select__item-icon fas fa-fw"
            :class="'fa-' + icon"
          />
          {{ name }}
        </slot>
      </div>
      <div v-if="description !== null" class="select__item-description">
        {{ description }}
      </div>
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
