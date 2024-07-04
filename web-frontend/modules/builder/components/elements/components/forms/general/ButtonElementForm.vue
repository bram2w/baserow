<template>
  <form @submit.prevent @keydown.enter.prevent>
    <CustomStyle
      v-model="values.styles"
      style-key="button"
      :config-block-types="['button']"
      :theme="builder.theme"
    />
    <ApplicationBuilderFormulaInputGroup
      v-model="values.value"
      :label="$t('buttonElementForm.valueLabel')"
      :placeholder="$t('buttonElementForm.valuePlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
    />
  </form>
</template>

<script>
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import CustomStyle from '@baserow/modules/builder/components/elements/components/forms/style/CustomStyle'
import elementForm from '@baserow/modules/builder/mixins/elementForm'

export default {
  name: 'ButtonElementForm',
  components: {
    ApplicationBuilderFormulaInputGroup,
    CustomStyle,
  },
  mixins: [elementForm],
  data() {
    return {
      values: {
        value: '',
        styles: {},
      },
      allowedValues: ['value', 'styles'],
    }
  },
}
</script>
