<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.link_name"
      small
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
import elementForm from '@baserow/modules/builder/mixins/elementForm'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import LinkNavigationSelectionForm from '@baserow/modules/builder/components/elements/components/forms/general/LinkNavigationSelectionForm'

export default {
  name: 'TextField',
  components: {
    ApplicationBuilderFormulaInputGroup,
    LinkNavigationSelectionForm,
  },
  mixins: [elementForm],
  inject: ['page', 'builder'],
  provide() {
    return {
      applicationContext: {
        builder: this.builder,
        page: this.page,
        element: this.element,
      },
    }
  },
  props: {
    element: {
      type: Object,
      required: true,
    },
  },
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
