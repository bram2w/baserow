<template>
  <div>
    <FieldNumberSubForm
      v-if="formulaType === 'number'"
      :default-values="defaultValues"
      :table="table"
      :allow-set-number-negative="false"
    >
    </FieldNumberSubForm>
    <FieldDateSubForm
      v-else-if="['date', 'last_modified', 'created_on'].includes(formulaType)"
      :default-values="defaultValues"
      :table="table"
    >
    </FieldDateSubForm>
  </div>
</template>
<script>
import FieldNumberSubForm from '@baserow/modules/database/components/field/FieldNumberSubForm'
import FieldDateSubForm from '@baserow/modules/database/components/field/FieldDateSubForm'
import form from '@baserow/modules/core/mixins/form'
import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'

export default {
  name: 'FormulaTypeSubForms',
  components: { FieldNumberSubForm, FieldDateSubForm },
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
