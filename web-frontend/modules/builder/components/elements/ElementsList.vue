<template>
  <ul v-auto-overflow-scroll class="select__items">
    <li v-for="element in elements" :key="element.id" class="select__item">
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
  },
}
</script>
