<template>
  <component :is="getComponent(field)" v-bind="$props" read-only></component>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import RowEditFieldDateReadOnly from '@baserow/modules/database/components/row/RowEditFieldDateReadOnly'
import RowEditFieldLongText from '@baserow/modules/database/components/row/RowEditFieldLongText'
import RowEditFieldText from '@baserow/modules/database/components/row/RowEditFieldText'
import RowEditFieldBoolean from '@baserow/modules/database/components/row/RowEditFieldBoolean'
import RowEditFieldNumber from '@baserow/modules/database/components/row/RowEditFieldNumber'
import RowEditFieldSingleSelectReadOnly from '@baserow/modules/database/components/row/RowEditFieldSingleSelectReadOnly'
import RowEditFieldBlank from '@baserow/modules/database/components/row/RowEditFieldBlank'
import RowEditFieldArray from '@baserow/modules/database/components/row/RowEditFieldArray'

export default {
  name: 'RowEditFieldFormula',
  components: {
    RowEditFieldDateReadOnly,
    RowEditFieldText,
    RowEditFieldLongText,
    RowEditFieldBoolean,
    RowEditFieldNumber,
    RowEditFieldBlank,
    RowEditFieldArray,
    RowEditFieldSingleSelectReadOnly,
  },
  mixins: [rowEditField],
  methods: {
    getComponent(field) {
      const formulaType = this.$registry.get('formula_type', field.formula_type)
      return formulaType.getRowEditFieldComponent(field)
    },
  },
}
</script>
