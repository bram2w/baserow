<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.label"
      :label="$t('generalForm.labelTitle')"
      :placeholder="$t('generalForm.labelPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS"
      class="margin-bottom-2"
    ></ApplicationBuilderFormulaInputGroup>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.default_value"
      :label="$t('generalForm.valueTitle')"
      :placeholder="$t('generalForm.valuePlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS"
      class="margin-bottom-2"
    ></ApplicationBuilderFormulaInputGroup>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.placeholder"
      :label="$t('generalForm.placeholderTitle')"
      :placeholder="$t('generalForm.placeholderPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS"
      class="margin-bottom-2"
    ></ApplicationBuilderFormulaInputGroup>

    <FormGroup
      :label="$t('generalForm.requiredTitle')"
      small-label
      required
      class="margin-bottom-2"
    >
      <Checkbox v-model="values.required"></Checkbox>
    </FormGroup>

    <FormGroup
      :label="$t('generalForm.validationTitle')"
      small-label
      required
      class="margin-bottom-2"
    >
      <Dropdown v-model="values.validation_type" :show-search="true" small>
        <DropdownItem
          v-for="validationType in validationTypes"
          :key="validationType.name"
          :name="validationType.label"
          :value="validationType.name"
          :description="validationType.description"
        >
        </DropdownItem>
      </Dropdown>
    </FormGroup>

    <FormGroup
      :label="$t('inputTextElementForm.multilineTitle')"
      small-label
      required
      class="margin-bottom-2"
    >
      <Checkbox v-model="values.is_multiline"></Checkbox>
    </FormGroup>

    <FormGroup
      v-if="values.is_multiline"
      small-label
      required
      class="margin-bottom-2"
      :error-message="
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
    >
      <FormInput
        v-model="values.rows"
        type="number"
        :label="$t('inputTextElementForm.rowsTitle')"
        :placeholder="$t('inputTextElementForm.rowsPlaceholder')"
        :to-value="(value) => parseInt(value)"
      ></FormInput>
    </FormGroup>

    <FormGroup
      v-else
      :label="$t('inputTextElementForm.inputType')"
      :helper-text="
        values.input_type === 'password'
          ? $t('inputTextElementForm.passwordTypeWarning')
          : null
      "
      small-label
      required
      class="margin-bottom-2"
    >
      <Dropdown v-model="values.input_type" :show-search="false" small>
        <DropdownItem
          v-for="inputType in inputTypes"
          :key="inputType.name"
          :name="inputType.label"
          :value="inputType.name"
          :description="inputType.description"
        >
        </DropdownItem>
      </Dropdown>
    </FormGroup>
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
        validation_type: 'any',
        placeholder: '',
        is_multiline: false,
        rows: 3,
        type: 'text',
      },
    }
  },
  computed: {
    validationTypes() {
      return [
        {
          name: 'any',
          label: this.$t('inputTextElementForm.validationTypeAnyLabel'),
          description: this.$t(
            'inputTextElementForm.validationTypeAnyDescription'
          ),
        },
        {
          name: 'integer',
          label: this.$t('inputTextElementForm.validationTypeIntegerLabel'),
          description: this.$t(
            'inputTextElementForm.validationTypeIntegerDescription'
          ),
        },
        {
          name: 'email',
          label: this.$t('inputTextElementForm.validationTypeEmailLabel'),
          description: this.$t(
            'inputTextElementForm.validationTypeEmailDescription'
          ),
        },
      ]
    },
    inputTypes() {
      return [
        {
          name: 'text',
          label: this.$t('inputTextElementForm.inputTypeTextLabel'),
        },
        {
          name: 'password',
          label: this.$t('inputTextElementForm.inputTypePasswordLabel'),
        },
      ]
    },
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
