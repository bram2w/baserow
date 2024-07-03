<template>
  <form @submit.prevent @keydown.enter.prevent>
    <CustomStyle
      v-if="values.variant === 'button'"
      v-model="values.styles"
      style-key="button"
      :config-block-types="['button']"
      :theme="builder.theme"
      :element="values"
    />
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
    <FormGroup :label="$t('linkElementForm.variant')">
      <div class="control__elements--flex">
        <RadioButton v-model="values.variant" value="link">
          {{ $t('linkElementForm.variantLink') }}
        </RadioButton>
        <RadioButton v-model="values.variant" value="button">
          {{ $t('linkElementForm.variantButton') }}
        </RadioButton>
      </div>
    </FormGroup>

    <HorizontalAlignmentSelector v-model="values.alignment" />

    <template v-if="values.variant === 'button'">
      <WidthSelector v-model="values.width" />
    </template>
  </form>
</template>

<script>
import HorizontalAlignmentSelector from '@baserow/modules/builder/components/elements/components/forms/general/settings/HorizontalAlignmentsSelector'
import { HORIZONTAL_ALIGNMENTS, WIDTHS } from '@baserow/modules/builder/enums'
import WidthSelector from '@baserow/modules/builder/components/elements/components/forms/general/settings/WidthSelector'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import elementForm from '@baserow/modules/builder/mixins/elementForm'
import LinkNavigationSelectionForm from '@baserow/modules/builder/components/elements/components/forms/general/LinkNavigationSelectionForm'

import CustomStyle from '@baserow/modules/builder/components/elements/components/forms/style/CustomStyle'

export default {
  name: 'LinkElementForm',
  components: {
    WidthSelector,
    ApplicationBuilderFormulaInputGroup,
    HorizontalAlignmentSelector,
    LinkNavigationSelectionForm,
    CustomStyle,
  },
  mixins: [elementForm],
  data() {
    return {
      values: {
        value: '',
        alignment: HORIZONTAL_ALIGNMENTS.LEFT.value,
        variant: 'link',
        width: WIDTHS.AUTO.value,
        styles: {},
      },
      allowedValues: ['value', 'alignment', 'variant', 'width', 'styles'],
    }
  },
}
</script>
