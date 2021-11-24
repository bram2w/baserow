<template>
  <div>
    <FieldFormulaNumberSubForm
      v-if="formulaType === 'number'"
      :default-values="defaultValues"
      :table="table"
    >
    </FieldFormulaNumberSubForm>
    <FieldDateSubForm
      v-else-if="['date', 'last_modified', 'created_on'].includes(formulaType)"
      :default-values="defaultValues"
      :table="table"
    >
    </FieldDateSubForm>
  </div>
</template>
<script>
import FieldFormulaNumberSubForm from '@baserow/modules/database/components/field/FieldFormulaNumberSubForm'
import FieldDateSubForm from '@baserow/modules/database/components/field/FieldDateSubForm'
import form from '@baserow/modules/core/mixins/form'
import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'

export default {
  name: 'FormulaTypeSubForms',
  components: { FieldFormulaNumberSubForm, FieldDateSubForm },
  mixins: [form, fieldSubForm],
  props: {
    table: {
      required: true,
      type: Object,
    },
    formulaType: {
      required: false,
      type: String,
      default: null,
    },
    defaultValues: {
      required: true,
      type: Object,
    },
  },
  data() {
    return {
      allowedValues: [],
      values: {},
    }
  },
}
</script>
