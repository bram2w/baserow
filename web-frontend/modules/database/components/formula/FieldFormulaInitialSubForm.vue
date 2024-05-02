<template>
  <div>
    <div class="control">
      <label class="control__label control__label--small">{{
        $t('fieldType.formula')
      }}</label>
      <div class="control__elements">
        <input
          ref="formulaInput"
          :value="formula"
          type="text"
          class="input input--small input--monospace"
          :placeholder="
            $t('fieldFormulaInitialSubForm.formulaInputPlaceholder')
          "
          @click="$emit('open-advanced-context', $refs.formulaInput)"
          @input="$emit('open-advanced-context', $refs.formulaInput)"
        />
        <component
          :is="component"
          v-for="(component, index) in additionalInputComponents"
          :key="index"
          :database="database"
          :table="table"
          @update-formula="$emit('update-formula', $event)"
        ></component>
        <div v-if="loading" class="loading"></div>
        <template v-else>
          <div v-if="error" class="error formula-field__error">
            {{ error }}
          </div>
          <div class="formula-field__refresh-link">
            <a
              v-if="formulaTypeRefreshNeeded"
              href="#"
              @click.stop="$emit('refresh-formula-type')"
            >
              <i class="iconoir-refresh-double"></i>
              {{ $t('fieldFormulaInitialSubForm.refreshFormulaOptions') }}
            </a>
          </div>
        </template>
      </div>
    </div>
    <template v-if="showTypeFormattingOptions">
      <FormulaTypeSubForms
        :default-values="defaultValues"
        :formula-type="formulaType"
        :table="table"
        :view="view"
        :all-fields-in-table="allFieldsInTable"
        :database="database"
        :primary="primary"
      >
      </FormulaTypeSubForms>
    </template>
  </div>
</template>
<script>
import form from '@baserow/modules/core/mixins/form'

import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'
import FormulaTypeSubForms from '@baserow/modules/database/components/formula/FormulaTypeSubForms'
import { FormulaFieldType } from '@baserow/modules/database/fieldTypes'

export default {
  name: 'FieldFormulaInitialSubForm',
  components: {
    FormulaTypeSubForms,
  },
  mixins: [form, fieldSubForm],
  props: {
    loading: {
      type: Boolean,
      required: true,
    },
    formula: {
      type: String,
      required: true,
    },
    formulaType: {
      type: String,
      required: false,
      default: null,
    },
    error: {
      type: String,
      required: false,
      default: null,
    },
    formulaTypeRefreshNeeded: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      allowedValues: [],
      values: {},
    }
  },
  computed: {
    showTypeFormattingOptions() {
      return !(this.loading || this.formulaTypeRefreshNeeded || this.error)
    },
    additionalInputComponents() {
      return this.$registry
        .get('field', FormulaFieldType.getType())
        .getAdditionalFormInputComponents()
    },
  },
}
</script>
