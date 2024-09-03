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
      <template #after-input>
        <CustomStyle
          v-model="values.styles"
          style-key="cell"
          :config-block-types="['table', 'button']"
          :theme="baseTheme"
          :extra-args="{ onlyCell: true, noAlignment: true }"
          variant="normal"
        />
      </template>
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
import CustomStyle from '@baserow/modules/builder/components/elements/components/forms/style/CustomStyle'
import LinkNavigationSelectionForm from '@baserow/modules/builder/components/elements/components/forms/general/LinkNavigationSelectionForm'

export default {
  name: 'TextField',
  components: {
    InjectedFormulaInput,
    CustomStyle,
    LinkNavigationSelectionForm,
  },
  mixins: [collectionFieldForm],
  data() {
    return {
      allowedValues: ['link_name', 'styles'],
      values: {
        link_name: '',
        styles: {},
      },
    }
  },
}
</script>
