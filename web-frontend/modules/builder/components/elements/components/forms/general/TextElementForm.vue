<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormGroup
      :label="$t('textElementForm.textFormatTypeLabel')"
      small-label
      required
      class="margin-bottom-2"
    >
      <RadioGroup
        v-model="values.format"
        type="button"
        :options="textFormatTypeOptions"
      >
      </RadioGroup>
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
      textFormatTypeOptions: [
        {
          value: TEXT_FORMAT_TYPES.PLAIN,
          label: this.$t('textElementForm.textFormatTypePlain'),
        },
        {
          value: TEXT_FORMAT_TYPES.MARKDOWN,
          label: this.$t('textElementForm.textFormatTypeMarkdown'),
        },
      ],
    }
  },
  computed: {
    TEXT_FORMAT_TYPES() {
      return TEXT_FORMAT_TYPES
    },
  },
}
</script>
