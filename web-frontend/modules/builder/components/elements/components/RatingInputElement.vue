<template>
  <ABFormGroup
    :label="labelResolved"
    :required="element.required"
    :error-message="displayFormDataError ? $t('error.requiredField') : ''"
  >
    <template #label>
      <FormattedText
        :content="labelResolved"
        :format="labelFormat"
        preset="inlineLinks"
      />
    </template>
    <Rating
      :value="inputValue"
      :max-value="element.max_value"
      :custom-color="resolveColor(element.color, colorVariables)"
      :rating-style="element.rating_style || 'star'"
      show-unselected
      @update="inputValue = $event"
    />
  </ABFormGroup>
</template>

<script>
import Rating from '@baserow/modules/database/components/Rating'
import FormattedText from '@baserow/modules/builder/components/FormattedText'
import { getFormulaFormat } from '@baserow/modules/core/formula/textFormat'
import formElement from '@baserow/modules/builder/mixins/formElement'
import { ensureString } from '@baserow/modules/core/utils/validator'
import { useVuelidate } from '@vuelidate/core'
import { required } from '@vuelidate/validators'

export default {
  name: 'RatingInputElement',
  components: {
    Rating,
    FormattedText,
  },
  mixins: [formElement],
  setup() {
    return { v$: useVuelidate() }
  },
  computed: {
    labelFormat() {
      return getFormulaFormat(this.element.label)
    },
    labelResolved() {
      return ensureString(this.resolveFormula(this.element.label))
    },
    rules() {
      return {
        formElementData: {
          value: this.element.required ? { required } : {},
        },
      }
    },
  },
  validations() {
    return this.rules
  },
}
</script>
