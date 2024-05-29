<template>
  <div v-if="!isDeactivated">
    <SelectAIModelForm
      :default-values="defaultValues"
      :database="database"
    ></SelectAIModelForm>
    <div class="control">
      <label class="control__label control__label--small">
        {{ $t('fieldAISubForm.prompt') }}
      </label>
      <div class="control__elements">
        <div style="max-width: 366px">
          <FormulaInputField
            v-model="values.ai_prompt"
            :data-providers="dataProviders"
            :application-context="applicationContext"
            placeholder="What is Baserow?"
          ></FormulaInputField>
        </div>
        <div
          v-if="$v.values.ai_prompt.$dirty && $v.values.ai_prompt.$error"
          class="error"
        >
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </div>
  </div>
  <div v-else>
    <p>
      {{ $t('fieldAISubForm.premiumFeature') }} <i class="iconoir-lock"></i>
    </p>
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'
import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'
import FormulaInputField from '@baserow/modules/core/components/formula/FormulaInputField'
import SelectAIModelForm from '@baserow/modules/core/components/ai/SelectAIModelForm'

export default {
  name: 'FieldAISubForm',
  components: { SelectAIModelForm, FormulaInputField },
  mixins: [form, fieldSubForm],
  data() {
    return {
      allowedValues: ['ai_prompt'],
      values: {
        ai_prompt: '',
      },
    }
  },
  computed: {
    // Return the reactive object that can be updated in runtime.
    workspace() {
      return this.$store.getters['workspace/get'](this.database.workspace.id)
    },
    applicationContext() {
      const context = {}
      Object.defineProperty(context, 'fields', {
        enumerable: true,
        get: () =>
          this.allFieldsInTable.filter((f) => {
            const isNotThisField = f.id !== this.defaultValues.id
            return isNotThisField
          }),
      })
      return context
    },
    dataProviders() {
      return [this.$registry.get('databaseDataProvider', 'fields')]
    },
    isDeactivated() {
      return this.$registry
        .get('field', this.fieldType)
        .isDeactivated(this.workspace.id)
    },
  },
  validations: {
    values: {
      ai_prompt: { required },
    },
  },
}
</script>
