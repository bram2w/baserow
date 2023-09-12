<template>
  <div>
    <PageRootElement
      v-for="element in elements"
      :key="element.id"
      :element="element"
      :mode="mode"
    />
  </div>
</template>

<script>
import PageRootElement from '@baserow/modules/builder/components/page/PageRootElement'

export default {
  components: { PageRootElement },
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
}
</script>
