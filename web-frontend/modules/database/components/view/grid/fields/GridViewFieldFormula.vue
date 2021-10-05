<template>
  <component
    :is="getComponent(field)"
    v-if="getComponent(field)"
    :field="field"
    :value="value"
    class="active"
  ></component>
  <div v-else class="grid-view__cell cell-error active">Unknown Field Type</div>
</template>

<script>
import FunctionalGridViewFieldDate from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldDate'
import FunctionalGridViewFieldBoolean from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldBoolean'
import FunctionalGridViewFieldNumber from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldNumber'
import FunctionalGridViewFieldText from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldText'
import gridField from '@baserow/modules/database/mixins/gridField'

export default {
  name: 'GridViewFormulaField',
  mixins: [gridField],
  methods: {
    getComponent(field) {
      return {
        date: FunctionalGridViewFieldDate,
        text: FunctionalGridViewFieldText,
        boolean: FunctionalGridViewFieldBoolean,
        number: FunctionalGridViewFieldNumber,
        invalid: FunctionalGridViewFieldText,
        char: FunctionalGridViewFieldText,
        date_interval: FunctionalGridViewFieldText,
      }[field.formula_type]
    },
  },
}
</script>
