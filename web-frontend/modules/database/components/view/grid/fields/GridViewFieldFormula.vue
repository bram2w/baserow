<template>
  <component
    :is="getComponent(field)"
    :field="field"
    :value="value"
    :read-only="true"
    :selected="selected"
    :store-prefix="storePrefix"
    class="active"
  ></component>
</template>

<script>
import baseField from '@baserow/modules/database/mixins/baseField'

export default {
  name: 'GridViewFieldFormula',
  mixins: [baseField],
  props: {
    selected: {
      type: Boolean,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
  },
  methods: {
    getComponent(field) {
      const formulaType = this.$registry.get('formula_type', field.formula_type)
      return formulaType.getGridViewFieldComponent()
    },
  },
}
</script>
