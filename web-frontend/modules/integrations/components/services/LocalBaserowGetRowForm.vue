<template>
  <form @submit.prevent>
    <div class="row">
      <div class="col col-6">
        <FormInput
          v-model="values.table_id"
          type="number"
          small-label
          :label="$t('localBaserowGetRowForm.tableFieldLabel')"
          :placeholder="$t('localBaserowGetRowForm.tableFieldPlaceHolder')"
          :from-value="(value) => (value ? value : '')"
          :to-value="(value) => (value ? value : null)"
        />
      </div>
      <div class="col col-6">
        <FormulaInputGroup
          v-model="values.row_id"
          small-label
          :label="$t('localBaserowGetRowForm.rowFieldLabel')"
          :placeholder="$t('localBaserowGetRowForm.rowFieldPlaceHolder')"
          :error="
            !$v.values.row_id.validFormula
              ? $t('localBaserowGetRowForm.invalidFormula')
              : ''
          "
        />
      </div>
    </div>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import FormulaInputGroup from '@baserow/modules/core/components/formula/FormulaInputGroup'
import { isValidFormula } from '@baserow/formula'

export default {
  components: { FormulaInputGroup },
  mixins: [form],
  props: {
    builder: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      allowedValues: ['table_id', 'row_id'],
      values: {
        table_id: null,
        row_id: '',
      },
    }
  },
  validations() {
    return {
      values: {
        row_id: { validFormula: isValidFormula },
      },
    }
  },
}
</script>
