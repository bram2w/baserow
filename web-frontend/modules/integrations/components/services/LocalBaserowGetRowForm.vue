<template>
  <form @submit.prevent>
    <div class="row">
      <div class="col col-4">
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
      <div class="col col-4">
        <FormInput
          v-model="values.view_id"
          type="number"
          small-label
          :label="$t('localBaserowGetRowForm.viewFieldLabel')"
          :placeholder="$t('localBaserowGetRowForm.viewFieldPlaceHolder')"
          :from-value="(value) => (value ? value : '')"
          :to-value="(value) => (value ? value : null)"
        />
      </div>
      <div class="col col-4">
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
    <div class="row">
      <div class="col col-12">
        <Tabs>
          <Tab :title="$t('localBaserowListRowsForm.searchTabTitle')">
            <FormInput
              v-model="values.search_query"
              type="text"
              small-label
              :placeholder="
                $t('localBaserowListRowsForm.searchFieldPlaceHolder')
              "
            />
          </Tab>
        </Tabs>
      </div>
    </div>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import FormulaInputGroup from '@baserow/modules/core/components/formula/FormulaInputGroup'
import { isValidFormula } from '@baserow/modules/core/formula'

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
      allowedValues: ['table_id', 'view_id', 'row_id', 'search_query'],
      values: {
        table_id: null,
        view_id: null,
        row_id: '',
        search_query: '',
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
