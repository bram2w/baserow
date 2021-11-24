<template>
  <component
    :is="getComponent(field)"
    :field="field"
    :value="value"
    :read-only="true"
    :selected="selected"
    class="active"
  ></component>
</template>

<script>
import gridField from '@baserow/modules/database/mixins/gridField'

export default {
  name: 'GridViewFormulaField',
  mixins: [gridField],
  methods: {
    getComponent(field) {
      const formulaType = this.$registry.get('formula_type', field.formula_type)
      return formulaType.getGridViewFieldComponent()
    },
  },
}
</script>
