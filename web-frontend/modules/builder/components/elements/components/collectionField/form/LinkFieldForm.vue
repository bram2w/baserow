<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormGroup
      small-label
      :label="$t('linkFieldForm.fieldLinkNameLabel')"
      class="margin-bottom-2"
      required
      horizontal
    >
      <InjectedFormulaInput
        v-model="values.link_name"
        :placeholder="$t('linkFieldForm.fieldLinkNamePlaceholder')"
      />
    </FormGroup>
    <LinkNavigationSelectionForm
      :default-values="defaultValues"
      @values-changed="emitChange($event)"
    />
  </form>
</template>

<script>
import collectionFieldForm from '@baserow/modules/builder/mixins/collectionFieldForm'
import InjectedFormulaInput from '@baserow/modules/core/components/formula/InjectedFormulaInput'
import LinkNavigationSelectionForm from '@baserow/modules/builder/components/elements/components/forms/general/LinkNavigationSelectionForm'

export default {
  name: 'TextField',
  components: {
    InjectedFormulaInput,
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
