<template>
  <div class="context__form-container">
    <FormGroup
      small-label
      :label="$t('selectAIModelForm.AIType')"
      :error="$v.values.ai_generative_ai_type.$error"
      required
    >
      <Dropdown
        v-model="values.ai_generative_ai_type"
        class="dropdown--floating"
        :error="$v.values.ai_generative_ai_type.$errors"
        :fixed-items="true"
        :show-search="false"
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
      <template #error>
        <div
          v-if="
            $v.values.ai_generative_ai_type.$dirty &&
            !$v.values.ai_generative_ai_type.required
          "
        >
          {{ $t('error.requiredField') }}
        </div>
      </template>
    </FormGroup>

    <FormGroup
      small-label
      :label="$t('selectAIModelForm.AIModel')"
      :error="$v.values.ai_generative_ai_model.$error"
      required
    >
      <Dropdown
        ref="aiModel"
        v-model="values.ai_generative_ai_model"
        class="dropdown--floating"
        :error="$v.values.ai_generative_ai_model.$error"
        :fixed-items="true"
        :show-search="false"
        @hide="$v.values.ai_generative_ai_model.$touch()"
      >
        <DropdownItem
          v-for="aIType in aIModelsPerType"
          :key="aIType"
          :name="aIType"
          :value="aIType"
        />
      </Dropdown>
      <template #error>
        <div
          v-if="
            $v.values.ai_generative_ai_model.$dirty &&
            !$v.values.ai_generative_ai_model.required
          "
        >
          {{ $t('error.requiredField') }}
        </div>
      </template>
    </FormGroup>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { required } from 'vuelidate/lib/validators'
import modal from '@baserow/modules/core/mixins/modal'
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'SelectAIModelForm',
  mixins: [form, modal],
  props: {
    database: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      allowedValues: ['ai_generative_ai_type', 'ai_generative_ai_model'],
      values: {
        ai_generative_ai_type: null,
        ai_generative_ai_model: null,
      },
    }
  },
  computed: {
    ...mapGetters({
      settings: 'settings/get',
    }),
    // Return the reactive object that can be updated in runtime.
    workspace() {
      return this.$store.getters['workspace/get'](this.database.workspace.id)
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
  },
  watch: {
    'values.ai_generative_ai_type': function (newValue, oldValue) {
      this.$emit('ai-type-changed', newValue)
    },
  },
  validations: {
    values: {
      ai_generative_ai_type: { required },
      ai_generative_ai_model: { required },
    },
  },
}
</script>
