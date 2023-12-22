<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.value"
      :label="$t('buttonElementForm.valueLabel')"
      :placeholder="$t('buttonElementForm.valuePlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
    />
    <FormElement class="control">
      <HorizontalAlignmentsSelector v-model="values.alignment" />
    </FormElement>
    <FormElement class="control">
      <WidthSelector v-model="values.width" />
    </FormElement>
    <ColorInputGroup
      v-model="values.button_color"
      :label="$t('buttonElementForm.buttonColor')"
      :color-variables="colorVariables"
    />
  </form>
</template>

<script>
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import { HORIZONTAL_ALIGNMENTS, WIDTHS } from '@baserow/modules/builder/enums'
import HorizontalAlignmentsSelector from '@baserow/modules/builder/components/elements/components/forms/general/settings/HorizontalAlignmentsSelector'
import WidthSelector from '@baserow/modules/builder/components/elements/components/forms/general/settings/WidthSelector'
import { themeToColorVariables } from '@baserow/modules/builder/utils/theme'
import elementForm from '@baserow/modules/builder/mixins/elementForm'

export default {
  name: 'ButtonElementForm',
  components: {
    WidthSelector,
    ApplicationBuilderFormulaInputGroup,
    HorizontalAlignmentsSelector,
  },
  mixins: [elementForm],
  data() {
    return {
      values: {
        value: '',
        alignment: HORIZONTAL_ALIGNMENTS.LEFT.value,
        width: WIDTHS.AUTO.value,
      },
    }
  },
  computed: {
    colorVariables() {
      return themeToColorVariables(this.builder.theme)
    },
  },
}
</script>
