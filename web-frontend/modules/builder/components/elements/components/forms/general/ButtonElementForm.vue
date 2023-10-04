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
  </form>
</template>

<script>
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import form from '@baserow/modules/core/mixins/form'
import {
  DATA_PROVIDERS_ALLOWED_ELEMENTS,
  HORIZONTAL_ALIGNMENTS,
  WIDTHS,
} from '@baserow/modules/builder/enums'
import HorizontalAlignmentsSelector from '@baserow/modules/builder/components/elements/components/forms/general/settings/HorizontalAlignmentsSelector'

import WidthSelector from '@baserow/modules/builder/components/elements/components/forms/general/settings/WidthSelector'

export default {
  name: 'ButtonElementForm',
  components: {
    WidthSelector,
    ApplicationBuilderFormulaInputGroup,
    HorizontalAlignmentsSelector,
  },
  mixins: [form],
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
    DATA_PROVIDERS_ALLOWED_ELEMENTS: () => DATA_PROVIDERS_ALLOWED_ELEMENTS,
  },
}
</script>
