<template>
  <component :is="component" v-bind="forwarded" class="active" />
</template>

<script>
import { unwrapLazyComponent } from '@baserow/modules/core/utils/lazyComponent'
export default {
  name: 'GridViewFieldFormula',
  inheritAttrs: false,
  props: {
    field: { type: Object, required: true },
  },
  computed: {
    forwarded() {
      return {
        ...this.$attrs,
        field: this.field,
        readOnly: true,
      }
    },
    component() {
      return unwrapLazyComponent(
        this.$registry
          .get('formula_type', this.field.formula_type)
          .getGridViewFieldComponent(this.field)
      )
    },
  },
}
</script>
