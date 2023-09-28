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
            class="select__item-icon"
            :class="icon"
          />
          <img v-if="image" class="select__item-image" :src="image" />
          <span class="select__item-name-text" :title="name">{{ name }}</span>
        </slot>
      </div>
      <div v-if="description !== null" class="select__item-description">
        {{ description }}
      </div>
      <i
        v-if="isActive(value)"
        class="select__item-active-icon iconoir-check-circle"
      ></i>
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
