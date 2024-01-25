<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.value"
      :label="$t('textElementForm.textTitle')"
      :placeholder="$t('textElementForm.textPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
    />
    <FormElement class="control">
      <HorizontalAlignmentsSelector v-model="values.alignment" />
    </FormElement>
  </form>
</template>

<script>
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import elementForm from '@baserow/modules/builder/mixins/elementForm'
import { HORIZONTAL_ALIGNMENTS } from '@baserow/modules/builder/enums'
import HorizontalAlignmentsSelector from '@baserow/modules/builder/components/elements/components/forms/general/settings/HorizontalAlignmentsSelector.vue'

export default {
  name: 'TextElementForm',
  components: {
    HorizontalAlignmentsSelector,
    ApplicationBuilderFormulaInputGroup,
  },
  mixins: [elementForm],
  data() {
    return {
      values: {
        value: '',
        alignment: HORIZONTAL_ALIGNMENTS.LEFT.value,
      },
    }
  },
}
</script>
