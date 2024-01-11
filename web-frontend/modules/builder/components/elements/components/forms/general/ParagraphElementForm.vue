<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.value"
      :label="$t('paragraphElementForm.textTitle')"
      :placeholder="$t('elementForms.textInputPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
    />
  </form>
</template>

<script>
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import elementForm from '@baserow/modules/builder/mixins/elementForm'

export default {
  name: 'ParagraphElementForm',
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
