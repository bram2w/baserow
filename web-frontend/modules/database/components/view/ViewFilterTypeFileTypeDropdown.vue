<template>
  <Dropdown
    :value="filter.value"
    :show-search="false"
    :disabled="disabled"
    class="filters__value-dropdown dropdown--tiny"
    @input="$emit('input', $event)"
  >
    <DropdownItem
      :name="$t('viewFilterFileTypeDropdown.image')"
      value="image"
    ></DropdownItem>
    <DropdownItem
      :name="$t('viewFilterFileTypeDropdown.document')"
      value="document"
    ></DropdownItem>
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

<i18n>
{
  "en": {
    "viewFilterFileTypeDropdown": {
      "image": "Image",
      "document": "Document"
    }
  },
  "fr": {
    "viewFilterFileTypeDropdown": {
      "image": "Image",
      "document": "Document"
    }
  }
}
</i18n>
