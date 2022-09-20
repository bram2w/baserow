<template>
  <div class="control__elements">
    <FunctionalFormulaArrayItems
      class="row-edit-array-field"
      :field="field"
      :value="value"
      :selected="true"
    >
    </FunctionalFormulaArrayItems>
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import FunctionalFormulaArrayItems from '@baserow/modules/database/components/formula/array/FunctionalFormulaArrayItems'

export default {
  name: 'RowEditFieldArray',
  components: {
    FunctionalFormulaArrayItems,
  },
  mixins: [rowEditField],
}
</script>
