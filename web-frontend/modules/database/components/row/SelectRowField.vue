<template>
  <component
    :is="getFieldComponent(field.type)"
    :field="field"
    :value="row['field_' + field.id]"
    :selected="false"
    :state="{}"
    :read-only="true"
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
      return this.$registry
        .get('field', type)
        .getFunctionalGridViewFieldComponent()
    },
  },
}
</script>
