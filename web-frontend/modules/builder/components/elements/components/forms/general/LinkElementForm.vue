<template>
  <form @submit.prevent @keydown.enter.prevent>
    <CustomStyle
      v-if="values.variant === 'button'"
      v-model="values.styles"
      style-key="button"
      :config-block-types="['button']"
      :theme="builder.theme"
    />
    <CustomStyle
      v-else
      v-model="values.styles"
      style-key="link"
      :config-block-types="['link']"
      :theme="builder.theme"
    />
    <ApplicationBuilderFormulaInputGroup
      v-model="values.value"
      class="margin-bottom-2"
      :label="$t('linkElementForm.text')"
      small-label
      required
      :placeholder="$t('linkElementForm.textPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
    />
    <LinkNavigationSelectionForm
      :default-values="defaultValues"
      @values-changed="emitChange($event)"
    />
    <FormGroup
      :label="$t('linkElementForm.variant')"
      small-label
      required
      class="margin-bottom-2"
    >
      <RadioGroup
        v-model="values.variant"
        :options="linkElementFormVariantOptions"
        type="button"
      >
      </RadioGroup>
    </FormGroup>
  </form>
</template>

<script>
import {
  HORIZONTAL_ALIGNMENTS,
  WIDTHS_NEW,
} from '@baserow/modules/builder/enums'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import elementForm from '@baserow/modules/builder/mixins/elementForm'
import LinkNavigationSelectionForm from '@baserow/modules/builder/components/elements/components/forms/general/LinkNavigationSelectionForm'

import CustomStyle from '@baserow/modules/builder/components/elements/components/forms/style/CustomStyle'

export default {
  name: 'LinkElementForm',
  components: {
    ApplicationBuilderFormulaInputGroup,
    LinkNavigationSelectionForm,
    CustomStyle,
  },
  mixins: [elementForm],
  data() {
    return {
      values: {
        value: '',
        alignment: HORIZONTAL_ALIGNMENTS.LEFT,
        variant: 'link',
        width: WIDTHS_NEW.AUTO,
        styles: {},
      },
      allowedValues: ['value', 'alignment', 'variant', 'width', 'styles'],
      linkElementFormVariantOptions: [
        { value: 'link', label: this.$t('linkElementForm.variantLink') },
        { value: 'button', label: this.$t('linkElementForm.variantButton') },
      ],
    }
  },
}
</script>
