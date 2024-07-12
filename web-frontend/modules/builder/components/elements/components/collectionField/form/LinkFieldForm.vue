<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.link_name"
      :label="$t('linkFieldForm.fieldLinkNameLabel')"
      :placeholder="$t('linkFieldForm.fieldLinkNamePlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
      horizontal
    />
    <LinkNavigationSelectionForm
      :default-values="defaultValues"
      @values-changed="emitChange($event)"
    />
  </form>
</template>

<script>
import collectionFieldForm from '@baserow/modules/builder/mixins/collectionFieldForm'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import LinkNavigationSelectionForm from '@baserow/modules/builder/components/elements/components/forms/general/LinkNavigationSelectionForm'

export default {
  name: 'TextField',
  components: {
    ApplicationBuilderFormulaInputGroup,
    LinkNavigationSelectionForm,
  },
  mixins: [collectionFieldForm],
  data() {
    return {
      allowedValues: ['link_name'],
      values: {
        link_name: '',
      },
    }
  },
}
</script>
