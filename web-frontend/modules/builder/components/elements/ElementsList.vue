<template>
  <ul v-auto-overflow-scroll class="select__items">
    <li
      v-for="{ element, indented } in elementsAndChildren"
      :key="element.id"
      :class="{
        'select__item--selected': element.id === elementSelectedId,
        'select__item--indented': indented,
      }"
      class="select__item"
    >
      <ElementsListItem :element="element" @click="$emit('select', element)" />
    </li>
  </ul>
</template>

<script>
import ElementsListItem from '@baserow/modules/builder/components/elements/ElementsListItem'
export default {
  name: 'ElementsList',
  components: { ElementsListItem },
  props: {
    elements: {
      type: Array,
      required: true,
    },
    elementSelected: {
      type: Object,
      required: false,
      default: null,
    },
  },
  computed: {
    elementSelectedId() {
      return this.elementSelected ? this.elementSelected.id : null
    },
    elementsAndChildren() {
      return this.elements.reduce((acc, element) => {
        acc.push({ element, indented: false })

        const children = this.getChildren(element)
        if (children.length) {
          acc.push(
            ...children.map((child) => ({ element: child, indented: true }))
          )
        }

        return acc
      }, [])
    },
  },
  methods: {
    getChildren(element) {
      return this.$store.getters['element/getChildren'](element)
    },
  },
}
</script>
