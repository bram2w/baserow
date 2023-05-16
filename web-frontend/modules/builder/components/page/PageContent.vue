<template>
  <div>
    <component
      :is="getType(element).component"
      v-for="element in elements"
      :key="element.id"
      :element="element"
      class="element__component"
      :builder="builder"
      :mode="mode"
    />
  </div>
</template>

<script>
export default {
  inject: ['builder', 'mode'],
  props: {
    page: {
      type: Object,
      required: true,
    },
    path: {
      type: String,
      required: true,
    },
    params: {
      type: Object,
      required: true,
    },
    elements: {
      type: Array,
      required: true,
    },
  },
  methods: {
    getType(element) {
      return this.$registry.get('element', element.type)
    },
  },
}
</script>
