<template>
  <form @submit.prevent @keydown.enter.prevent>
    <CustomStyle
      v-model="values.styles"
      style-key="button"
      :config-block-types="['button']"
      :theme="builder.theme"
      :element="values"
    />
    <ApplicationBuilderFormulaInputGroup
      v-model="values.value"
      :label="$t('buttonElementForm.valueLabel')"
      :placeholder="$t('buttonElementForm.valuePlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
    />
    <HorizontalAlignmentsSelector v-model="values.alignment" />
    <WidthSelector v-model="values.width" />
  </form>
</template>

<script>
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import { HORIZONTAL_ALIGNMENTS, WIDTHS } from '@baserow/modules/builder/enums'
import CustomStyle from '@baserow/modules/builder/components/elements/components/forms/style/CustomStyle'
import HorizontalAlignmentsSelector from '@baserow/modules/builder/components/elements/components/forms/general/settings/HorizontalAlignmentsSelector'
import WidthSelector from '@baserow/modules/builder/components/elements/components/forms/general/settings/WidthSelector'
import elementForm from '@baserow/modules/builder/mixins/elementForm'

export default {
  name: 'ButtonElementForm',
  components: {
    WidthSelector,
    ApplicationBuilderFormulaInputGroup,
    HorizontalAlignmentsSelector,
    CustomStyle,
  },
  mixins: [elementForm],
  data() {
    return {
      values: {
        value: '',
        alignment: HORIZONTAL_ALIGNMENTS.LEFT.value,
        width: WIDTHS.AUTO.value,
        styles: {},
      },
      allowedValues: ['value', 'alignment', 'width', 'styles'],
    }
  },
}
</script>
