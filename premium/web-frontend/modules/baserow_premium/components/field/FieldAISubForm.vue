<template>
  <div v-if="!isDeactivated">
    <div class="control">
      <label class="control__label control__label--small">{{
        $t('fieldAISubForm.AIType')
      }}</label>
      <div class="control__elements">
        <Dropdown
          v-model="values.ai_generative_ai_type"
          class="dropdown--floating"
          :class="{
            'dropdown--error': $v.values.ai_generative_ai_type.$error,
          }"
          :fixed-items="true"
          :show-search="false"
          small
          @hide="$v.values.ai_generative_ai_type.$touch()"
          @change="$refs.aiModel.select(aIModelsPerType[0])"
        >
          <DropdownItem
            v-for="aIType in aITypes"
            :key="aIType"
            :name="aIType"
            :value="aIType"
          />
        </Dropdown>
      </div>
    </div>
    <div class="control">
      <label class="control__label control__label--small">
        {{ $t('fieldAISubForm.AIModel') }}
      </label>
      <div class="control__elements">
        <Dropdown
          ref="aiModel"
          v-model="values.ai_generative_ai_model"
          class="dropdown--floating"
          :class="{
            'dropdown--error': $v.values.ai_generative_ai_model.$error,
          }"
          :fixed-items="true"
          :show-search="false"
          small
          @hide="$v.values.ai_generative_ai_model.$touch()"
        >
          <DropdownItem
            v-for="aIType in aIModelsPerType"
            :key="aIType"
            :name="aIType"
            :value="aIType"
          />
        </Dropdown>
      </div>
    </div>
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

export default {
  name: 'FieldAISubForm',
  components: { FormulaInputField },
  mixins: [form, fieldSubForm],
  data() {
    return {
      allowedValues: [
        'ai_generative_ai_type',
        'ai_generative_ai_model',
        'ai_prompt',
      ],
      values: {
        ai_generative_ai_type: null,
        ai_generative_ai_model: null,
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
    aITypes() {
      return Object.keys(this.workspace.generative_ai_models_enabled || {})
    },
    aIModelsPerType() {
      return (
        this.workspace.generative_ai_models_enabled[
          this.values.ai_generative_ai_type
        ] || []
      )
    },
    isDeactivated() {
      return this.$registry
        .get('field', this.fieldType)
        .isDeactivated(this.workspace.id)
    },
  },
  validations: {
    values: {
      ai_generative_ai_type: { required },
      ai_generative_ai_model: { required },
      ai_prompt: { required },
    },
  },
}
</script>
