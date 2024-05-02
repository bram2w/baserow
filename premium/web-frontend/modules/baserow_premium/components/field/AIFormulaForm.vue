<template>
  <form @submit.prevent="submit">
    <SelectAIModelForm
      :database="database"
      :default-values="defaultValues"
    ></SelectAIModelForm>
    <div class="control">
      <label class="control__label control__label--small">{{
        $t('aiFormulaModal.label')
      }}</label>
      <div class="control__description">
        {{ $t('aiFormulaModal.labelDescription') }}
      </div>
      <div class="control__elements">
        <div>
          <textarea
            v-model="values.ai_prompt"
            type="text"
            class="input field-long-text"
            :class="{
              'input--error':
                $v.values.ai_prompt.$dirty && $v.values.ai_prompt.$error,
            }"
            @input="$v.values.ai_prompt.$touch()"
          ></textarea>
        </div>
        <div
          v-if="$v.values.ai_prompt.$error && !$v.values.ai_prompt.maxLength"
          class="error"
        >
          {{
            $t('error.maxLength', {
              max: $v.values.ai_prompt.$params.maxLength.max,
            })
          }}
        </div>
        <div
          v-if="$v.values.ai_prompt.$error && !$v.values.ai_prompt.required"
          class="error"
        >
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </div>
    <div class="align-right">
      <slot></slot>
    </div>
  </form>
</template>

<script>
import SelectAIModelForm from '@baserow/modules/core/components/ai/SelectAIModelForm'
import { required, maxLength } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'AIFormulaForm',
  components: { SelectAIModelForm },
  mixins: [form],
  props: {
    database: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      allowedValues: ['ai_prompt'],
      values: {
        ai_prompt: '',
      },
    }
  },
  validations: {
    values: {
      ai_prompt: {
        required,
        maxLength: maxLength(1000),
      },
    },
  },
}
</script>
