<template>
  <form @submit.prevent @keydown.enter.prevent>
    <CustomStyle
      v-model="values.styles"
      style-key="button"
      :config-block-types="['button']"
      :theme="builder.theme"
    />
    <ApplicationBuilderFormulaInputGroup
      v-model="values.submit_button_label"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
      :label="$t('formContainerElementForm.submitButtonLabel')"
      :placeholder="$t('formContainerElementForm.submitButtonPlaceholder')"
    />
    <FormGroup
      :label="$t('formContainerElementForm.resetToInitialValuesTitle')"
      :description="
        $t('formContainerElementForm.resetToInitialValuesDescription')
      "
    >
      <Checkbox
        v-model="values.reset_initial_values_post_submission"
      ></Checkbox>
    </FormGroup>
  </form>
</template>

<script>
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup.vue'
import elementForm from '@baserow/modules/builder/mixins/elementForm'
import CustomStyle from '@baserow/modules/builder/components/elements/components/forms/style/CustomStyle'

export default {
  name: 'FormContainerElementForm',
  components: { ApplicationBuilderFormulaInputGroup, CustomStyle },
  mixins: [elementForm],
  data() {
    return {
      values: {
        submit_button_label: '',
        reset_initial_values_post_submission: false,
        styles: {},
      },
      allowedValues: [
        'submit_button_label',
        'reset_initial_values_post_submission',
        'styles',
      ],
    }
  },
}
</script>
