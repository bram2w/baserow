<template>
  <ul class="list">
    <li v-for="(item, index) in items" :key="index" class="list__item">
      <div class="list__left-side">
        <checkbox
          v-if="selectable"
          :value="selectedItemsIndexes.includes(index)"
          @input="selected($event, item, index)"
        />
        <slot name="left-side" :item="item"></slot>
      </div>
      <div v-for="attribute in attributesValidated" :key="attribute">
        {{ item[attribute] }}
      </div>
      <slot name="right-side" :item="item"></slot>
    </li>
  </ul>
</template>

<script>
export default {
  name: 'List',
  props: {
    items: {
      type: Array,
      required: false,
      default: () => [],
    },
    attributes: {
      type: Array,
      required: false,
      default: () => null,
    },
    selectable: {
      type: Boolean,
      required: false,
      default: () => false,
    },
  },
  data() {
    return {
      selectedItemsIndexes: [],
    }
  },
  computed: {
    /**
     * If no attributes are provided as a prop we will just use all the attributes
     * of the first item
     */
    attributesValidated() {
      if (this.items.length) {
        return this.attributes ?? Object.keys(this.items[0])
      }
      return []
    },
  },
  methods: {
    selected(value, item, index) {
      if (value) {
        this.selectedItemsIndexes.push(index)
      } else {
        this.selectedItemsIndexes.splice(
          this.selectedItemsIndexes.indexOf(index),
          1
        )
      }
      this.$emit('selected', { value, item, index })
    },
  },
}
</script>
