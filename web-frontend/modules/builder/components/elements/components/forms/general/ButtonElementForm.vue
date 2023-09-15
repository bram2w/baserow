<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormulaInputGroup
      v-model="values.value"
      :label="$t('buttonElementForm.valueLabel')"
      :placeholder="$t('buttonElementForm.valuePlaceholder')"
    ></FormulaInputGroup>
    <FormElement class="control">
      <HorizontalAlignmentsSelector v-model="values.alignment" />
    </FormElement>
    <FormElement class="control">
      <WidthSelector v-model="values.width" />
    </FormElement>
  </form>
</template>

<script>
import FormulaInputGroup from '@baserow/modules/core/components/formula/FormulaInputGroup'
import form from '@baserow/modules/core/mixins/form'
import HorizontalAlignmentsSelector from '@baserow/modules/builder/components/elements/components/forms/general/settings/HorizontalAlignmentsSelector'
import { HORIZONTAL_ALIGNMENTS, WIDTHS } from '@baserow/modules/builder/enums'
import WidthSelector from '@baserow/modules/builder/components/elements/components/forms/general/settings/WidthSelector'

export default {
  name: 'ButtonElementForm',
  components: {
    WidthSelector,
    FormulaInputGroup,
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
}
</script>
