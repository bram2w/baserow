<template>
  <div>Grid view: {{ view.name }}</div>
</template>

<script>
export default {
  name: 'GridView',
  props: {
    view: {
      type: Object,
      required: true
    },
    table: {
      type: Object,
      required: true
    },
    database: {
      type: Object,
      required: true
    }
  }
}
</script>
