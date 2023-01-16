<template>
  <div class="crud-table-filters__filter-wrapper">
    <div class="crud-table-filters__filter-wrapper-title">{{ name }}</div>
    <slot></slot>
  </div>
</template>

<script>
export default {
  name: 'FilterWrapper',
  props: {
    name: {
      type: String,
      required: true,
    },
  },
}
</script>
