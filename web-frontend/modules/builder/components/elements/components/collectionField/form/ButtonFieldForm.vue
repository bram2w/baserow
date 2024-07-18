<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.label"
      :label="$t('generalForm.labelTitle')"
      :placeholder="$t('buttonFieldForm.labelPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
      horizontal
      class="margin-bottom-2"
    />
    <Alert>
      {{ $t('buttonFieldForm.infoMessage') }}
    </Alert>
  </form>
</template>

<script>
import collectionFieldForm from '@baserow/modules/builder/mixins/collectionFieldForm'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'

export default {
  name: 'ButtonFieldForm',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [collectionFieldForm],
  data() {
    return {
      allowedValues: ['label'],
      values: {
        label: '',
      },
    }
  },
}
</script>
