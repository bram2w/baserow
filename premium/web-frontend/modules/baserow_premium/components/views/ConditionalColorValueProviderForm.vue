<template>
  <div class="margin-bottom-2">Not available yet!</div>
</template>

<script>
export default {
  name: 'ConditionalColorValueProvider',
  components: {},
  props: {
    options: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  computed: {},
}
</script>
