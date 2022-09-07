<template>
  <li
    class="select-collaborators__dropdown-item"
    :class="{
      hidden: !isVisible(query),
      active: isActive(value),
      disabled: disabled,
      hover: isHovering(value),
    }"
  >
    <a
      class="select-collaborators__dropdown-link"
      @click="select(value, disabled)"
      @mousemove="hover(value, disabled)"
    >
      <div class="select-collaborators__initials">{{ initial(name) }}</div>
      <div class="select-collaborators__dropdown-option">
        {{ name }}
      </div>
    </a>
  </li>
</template>

<script>
import dropdownItem from '@baserow/modules/core/mixins/dropdownItem'

export default {
  name: 'FieldCollaboratorDropdownItem',
  mixins: [dropdownItem],
  methods: {
    initial(name) {
      return name.slice(0, 1).toUpperCase()
    },
  },
}
</script>
