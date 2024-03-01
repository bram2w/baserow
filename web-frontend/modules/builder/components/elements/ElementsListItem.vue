<template>
  <a class="select__item-link" @click="$emit('click')">
    <span class="select__item-name">
      <i :class="`${elementType.iconClass} select__item-icon`"></i>
      <span class="select__item-name-text">{{
        elementType.getDisplayName(element, applicationContext)
      }}</span>
    </span>
  </a>
</template>

<script>
export default {
  name: 'ElementsListItem',
  inject: ['builder', 'page', 'mode'],
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
    applicationContext() {
      return {
        builder: this.builder,
        page: this.page,
        mode: this.mode,
        element: this.element,
      }
    },
  },
}
</script>
