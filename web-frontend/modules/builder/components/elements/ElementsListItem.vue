<template>
  <a class="select__item-link" @click="$emit('click')">
    <span class="select__item-name">
      <i :class="`fas fa-${elementType.iconClass} select__item-icon`"></i>
      {{ elementType.name }}
    </span>
  </a>
</template>

<script>
export default {
  name: 'ElementsListItem',
  props: {
    element: {
      type: Object,
      required: true,
    },
  },
  computed: {
    elementType() {
      return this.$registry.get('element', this.element.type)
    },
  },
}
</script>
