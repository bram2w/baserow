<template>
  <div
    class="expandable-card"
    :class="{ ['expandable-card--expanded']: expanded }"
  >
    <div class="expandable-card__header">
      <slot name="header" :toggle="toggle" :expanded="expanded" />
    </div>
    <div v-if="expanded" class="expandable-card__content">
      <slot :toggle="toggle" :expanded="expanded" />
    </div>
  </div>
</template>

<script>
export default {
  name: 'ExpandableCard',
  props: {
    defaultExpanded: {
      type: Boolean,
      required: false,
      default: false,
    },
    forceExpanded: {
      type: Boolean,
      required: false,
      default: null,
    },
  },
  data() {
    return { expandedState: this.defaultExpanded }
  },
  computed: {
    expanded() {
      if (this.forceExpanded !== null) {
        return this.forceExpanded
      } else {
        return this.expandedState
      }
    },
  },
  methods: {
    toggle() {
      this.expandedState = !this.expandedState
    },
  },
}
</script>
