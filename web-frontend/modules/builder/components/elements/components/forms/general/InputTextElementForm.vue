<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.label"
      :label="$t('generalForm.labelTitle')"
      :placeholder="$t('generalForm.labelPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS"
    ></ApplicationBuilderFormulaInputGroup>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.default_value"
      :label="$t('generalForm.valueTitle')"
      :placeholder="$t('generalForm.valuePlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS"
    ></ApplicationBuilderFormulaInputGroup>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.placeholder"
      :label="$t('generalForm.placeholderTitle')"
      :placeholder="$t('generalForm.placeholderPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS"
    ></ApplicationBuilderFormulaInputGroup>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('generalForm.requiredTitle') }}
      </label>
      <div class="control__elements">
        <Checkbox v-model="values.required"></Checkbox>
      </div>
    </FormElement>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('inputTextElementForm.multilineTitle') }}
      </label>
      <div class="control__elements">
        <Checkbox v-model="values.is_multiline"></Checkbox>
      </div>
    </FormElement>
    <FormElement v-if="values.is_multiline">
      <FormInput
        v-model="values.rows"
        type="number"
        :label="$t('inputTextElementForm.rowsTitle')"
        :placeholder="$t('inputTextElementForm.rowsPlaceholder')"
        :to-value="(value) => parseInt(value)"
        :error="
          $v.values.rows.$dirty && !$v.values.rows.required
            ? $t('error.requiredField')
            : !$v.values.rows.integer
            ? $t('error.integerField')
            : !$v.values.rows.minValue
            ? $t('error.minValueField', { min: 1 })
            : !$v.values.rows.maxValue
            ? $t('error.maxValueField', { max: 100 })
            : ''
        "
      ></FormInput>
    </FormElement>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup.vue'
import elementForm from '@baserow/modules/builder/mixins/elementForm'
import { required, integer, minValue, maxValue } from 'vuelidate/lib/validators'

export default {
  name: 'InputTextElementForm',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [elementForm],
  data() {
    return {
      values: {
        label: '',
        default_value: '',
        required: false,
        placeholder: '',
        is_multiline: false,
        rows: 3,
      },
    }
  },
  methods: {
    emitChange(newValues) {
      if (this.isFormValid()) {
        form.methods.emitChange.bind(this)(newValues)
      }
    },
  },
  validations() {
    return {
      values: {
        rows: {
          required,
          integer,
          minValue: minValue(1),
          maxValue: maxValue(100),
        },
      },
    }
  },
}
</script>
