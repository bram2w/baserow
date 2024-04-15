<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.value"
      :label="$t('linkElementForm.text')"
      :placeholder="$t('linkElementForm.textPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
    />
    <LinkNavigationSelectionForm
      :default-values="defaultValues"
      @values-changed="emitChange($event)"
    />
    <FormElement class="control">
      <label class="control__label">
        {{ $t('linkElementForm.variant') }}
      </label>
      <div class="control__elements">
        <RadioButton v-model="values.variant" value="link">
          {{ $t('linkElementForm.variantLink') }}
        </RadioButton>
        <RadioButton v-model="values.variant" value="button">
          {{ $t('linkElementForm.variantButton') }}
        </RadioButton>
      </div>
    </FormElement>
    <FormElement class="control">
      <HorizontalAlignmentSelector v-model="values.alignment" />
    </FormElement>
    <FormElement v-if="values.variant === 'button'" class="control">
      <WidthSelector v-model="values.width" />
    </FormElement>
    <ColorInputGroup
      v-if="values.variant === 'button'"
      v-model="values.button_color"
      :label="$t('linkElementForm.buttonColor')"
      :color-variables="colorVariables"
    />
  </form>
</template>

<script>
import HorizontalAlignmentSelector from '@baserow/modules/builder/components/elements/components/forms/general/settings/HorizontalAlignmentsSelector'
import { HORIZONTAL_ALIGNMENTS, WIDTHS } from '@baserow/modules/builder/enums'
import WidthSelector from '@baserow/modules/builder/components/elements/components/forms/general/settings/WidthSelector'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import elementForm from '@baserow/modules/builder/mixins/elementForm'
import LinkNavigationSelectionForm from '@baserow/modules/builder/components/elements/components/forms/general/LinkNavigationSelectionForm'

export default {
  name: 'LinkElementForm',
  components: {
    WidthSelector,
    ApplicationBuilderFormulaInputGroup,
    HorizontalAlignmentSelector,
    LinkNavigationSelectionForm,
  },
  mixins: [elementForm],
  data() {
    return {
      values: {
        value: '',
        alignment: HORIZONTAL_ALIGNMENTS.LEFT.value,
        variant: 'link',
        width: WIDTHS.AUTO.value,
      },
      allowedValues: ['value', 'alignment', 'variant', 'width'],
    }
  },
}
</script>
