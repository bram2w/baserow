<template>
  <Dropdown
    :value="filter.value"
    :show-search="false"
    :disabled="readOnly"
    class="filters__value-dropdown dropdown--tiny"
    @input="$emit('input', $event)"
  >
    <DropdownItem name="image" value="image"></DropdownItem>
    <DropdownItem name="document" value="document"></DropdownItem>
  </Dropdown>
</template>

<script>
export default {
  name: 'ViewFilterTypeFileTypeDropdown',
  props: {
    filter: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    primary: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
}
</script>
