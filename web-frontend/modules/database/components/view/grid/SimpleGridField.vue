<template>
  <component
    :is="getFieldComponent(field.type)"
    :row="row"
    :field="field"
    :value="row[`field_${field.id}`]"
    :selected="false"
    :state="{}"
    :read-only="true"
  />
</template>

<script>
import { unwrapLazyComponent } from '@baserow/modules/core/utils/lazyComponent'
export default {
  name: 'SimpleGridField',
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
      return unwrapLazyComponent(
        this.$registry
          .get('field', type)
          .getFunctionalGridViewFieldComponent(this.field)
      )
    },
  },
}
</script>
