<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.url"
      :label="$t('linkFieldForm.fieldValueLabel')"
      :placeholder="$t('linkFieldForm.fieldValuePlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
      :application-context-additions="{
        element,
      }"
      horizontal
    />
    <ApplicationBuilderFormulaInputGroup
      v-model="values.link_name"
      :label="$t('linkFieldForm.fieldLinkNameLabel')"
      :placeholder="$t('linkFieldForm.fieldLinkNamePlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
      :application-context-additions="{
        element,
      }"
      horizontal
    />
  </form>
</template>

<script>
import { DATA_PROVIDERS_ALLOWED_ELEMENTS } from '@baserow/modules/builder/enums'
import form from '@baserow/modules/core/mixins/form'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'

export default {
  name: 'TextField',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [form],
  props: {
    element: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      allowedValues: ['url', 'link_name'],
      values: {
        url: '',
        link_name: '',
      },
    }
  },
  computed: {
    DATA_PROVIDERS_ALLOWED_ELEMENTS() {
      return DATA_PROVIDERS_ALLOWED_ELEMENTS
    },
  },
}
</script>
