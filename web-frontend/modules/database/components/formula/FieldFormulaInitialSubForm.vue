<template>
  <div>
    <div class="control">
      <label class="control__label control__label--small">Formula</label>
      <div class="control__elements">
        <input
          ref="formulaInput"
          :value="formula"
          type="text"
          class="input input--monospace"
          placeholder="Click to edit the formula"
          @click="$emit('open-advanced-context', $refs.formulaInput)"
          @input="$emit('open-advanced-context', $refs.formulaInput)"
        />
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
              <i class="fas fa-sync-alt"></i>
              Refresh formula options
            </a>
          </div>
        </template>
      </div>
    </div>
    <template v-if="showTypeFormattingOptions">
      <FieldFormulaNumberSubForm
        v-if="formulaType === 'number'"
        :default-values="defaultValues"
        :table="table"
      >
      </FieldFormulaNumberSubForm>
      <FieldDateSubForm
        v-else-if="formulaType === 'date'"
        :default-values="defaultValues"
        :table="table"
      >
      </FieldDateSubForm>
    </template>
  </div>
</template>
<script>
import form from '@baserow/modules/core/mixins/form'

import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'
import FieldFormulaNumberSubForm from '@baserow/modules/database/components/field/FieldFormulaNumberSubForm'
import FieldDateSubForm from '@baserow/modules/database/components/field/FieldDateSubForm'

export default {
  name: 'FieldFormulaInitialSubForm',
  components: {
    FieldDateSubForm,
    FieldFormulaNumberSubForm,
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
  },
}
</script>
