<template>
  <form @submit.prevent @keydown.enter.prevent>
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

export default {
  name: 'TextElementForm',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [elementForm],
  data() {
    return {
      values: {
        value: '',
      },
    }
  },
}
</script>
