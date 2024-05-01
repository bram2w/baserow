<template>
  <li :key="element.id" class="elements-list__item">
    <a
      class="elements-list__item-link"
      :class="{
        'elements-list__item-link--selected': element.id === elementSelectedId,
      }"
      @click="$emit('select', element)"
    >
      <span class="elements-list__item-name">
        <i :class="`${elementType.iconClass} elements-list__item-icon`"></i>
        <span class="elements-list__item-name-text">{{
          elementType.getDisplayName(element, applicationContext)
        }}</span>
      </span>
    </a>
    <ElementsList
      v-if="filteredChildren.length"
      name="nested-elements-list"
      :elements="filteredChildren"
      :filtered-search-elements="filteredSearchElements"
      @select="$emit('select', $event)"
    ></ElementsList>
  </li>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'ElementsListItem',
  components: {
    ElementsList: () =>
      import('@baserow/modules/builder/components/elements/ElementsList'),
  },
  inject: ['builder', 'page', 'mode'],
  props: {
    element: {
      type: Object,
      required: true,
    },
    filteredSearchElements: {
      type: Array,
      required: false,
      default: () => [],
    },
  },
  computed: {
    ...mapGetters({
      elementSelected: 'element/getSelected',
    }),
    elementSelectedId() {
      return this.elementSelected ? this.elementSelected.id : null
    },
    elementType() {
      return this.$registry.get('element', this.element.type)
    },
    children() {
      return this.$store.getters['element/getChildren'](this.page, this.element)
    },
    /**
     * Responsible for returning elements to display in `ElementsList`.
     * If we've been given an array of `filteredSearchElements`, we'll filter
     * the elements to only include those that match the `id` of the element.
     * If `filteredSearchElements` is empty, then we show all `elements`.
     */
    filteredChildren() {
      if (this.filteredSearchElements.length === 0) {
        return this.children
      } else {
        return this.children.filter((child) => {
          return this.filteredSearchElements.includes(child.id)
        })
      }
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
