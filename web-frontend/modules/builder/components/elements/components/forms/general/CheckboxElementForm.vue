<template>
  <form @submit.prevent @keydown.enter.prevent>
    <CustomStyle
      v-model="values.styles"
      style-key="input"
      :config-block-types="['input']"
      :theme="builder.theme"
      :extra-args="{ onlyInput: true }"
    />
    <ApplicationBuilderFormulaInputGroup
      v-model="values.label"
      class="margin-bottom-2"
      small-label
      required
      :label="$t('checkboxElementForm.labelTitle')"
      :placeholder="$t('generalForm.labelPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS"
    ></ApplicationBuilderFormulaInputGroup>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.default_value"
      class="margin-bottom-2"
      small-label
      required
      :label="$t('checkboxElementForm.valueTitle')"
      :placeholder="$t('generalForm.valuePlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS"
    ></ApplicationBuilderFormulaInputGroup>
    <FormGroup
      small-label
      required
      :label="$t('checkboxElementForm.requiredTitle')"
    >
      <Checkbox v-model="values.required"></Checkbox>
    </FormGroup>
  </form>
</template>

<script>
import elementForm from '@baserow/modules/builder/mixins/elementForm'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup.vue'
import CustomStyle from '@baserow/modules/builder/components/elements/components/forms/style/CustomStyle'

export default {
  name: 'CheckboxElementForm',
  components: { ApplicationBuilderFormulaInputGroup, CustomStyle },
  mixins: [elementForm],
  data() {
    return {
      values: {
        label: '',
        default_value: '',
        required: false,
      },
    }
  },
}
</script>
