<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormGroup :label="$t('textElementForm.textFormatTypeLabel')">
      <RadioButton v-model="values.format" :value="TEXT_FORMAT_TYPES.PLAIN">
        {{ $t('textElementForm.textFormatTypePlain') }}
      </RadioButton>
      <RadioButton v-model="values.format" :value="TEXT_FORMAT_TYPES.MARKDOWN">
        {{ $t('textElementForm.textFormatTypeMarkdown') }}
      </RadioButton>
    </FormGroup>
    <CustomStyle
      v-model="values.styles"
      style-key="typography"
      :config-block-types="['typography']"
      :theme="builder.theme"
    />
    <ApplicationBuilderFormulaInputGroup
      v-model="values.value"
      :label="$t('textElementForm.textTitle')"
      :placeholder="$t('textElementForm.textPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
    />
  </form>
</template>

<script>
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import elementForm from '@baserow/modules/builder/mixins/elementForm'
import { TEXT_FORMAT_TYPES } from '@baserow/modules/builder/enums'
import CustomStyle from '@baserow/modules/builder/components/elements/components/forms/style/CustomStyle'

export default {
  name: 'TextElementForm',
  components: {
    ApplicationBuilderFormulaInputGroup,
    CustomStyle,
  },
  mixins: [elementForm],
  data() {
    return {
      values: {
        value: '',
        format: TEXT_FORMAT_TYPES.PLAIN,
        styles: {},
      },
    }
  },
  computed: {
    TEXT_FORMAT_TYPES() {
      return TEXT_FORMAT_TYPES
    },
  },
}
</script>
