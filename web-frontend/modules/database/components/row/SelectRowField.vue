<template>
  <component
    :is="getFieldComponent(field.type)"
    ref="field"
    :field="field"
    :value="row['field_' + field.id]"
    :selected="false"
  />
</template>

<script>
export default {
  name: 'SelectRowField',
  props: {
    field: {
      type: Object,
      required: true,
    },
    row: {
      type: Object,
      required: true,
    },
  },
  methods: {
    getFieldComponent(type) {
      return this.$registry.get('field', type).getGridViewFieldComponent()
    },
  },
}
</script>
