<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.submit_button_label"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
      :label="$t('formContainerElementForm.submitButtonLabel')"
      :placeholder="$t('formContainerElementForm.submitButtonPlaceholder')"
    />
    <ColorInputGroup
      v-model="values.button_color"
      :label="$t('formContainerElementForm.buttonColor')"
      :color-variables="colorVariables"
    />
  </form>
</template>

<script>
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup.vue'
import elementForm from '@baserow/modules/builder/mixins/elementForm'

export default {
  name: 'FormContainerElementForm',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [elementForm],
  data() {
    return {
      values: {
        submit_button_label: '',
      },
    }
  },
}
</script>
