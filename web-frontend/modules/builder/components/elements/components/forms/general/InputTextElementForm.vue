<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.default_value"
      :label="$t('inputTextElementForm.valueTitle')"
      :placeholder="$t('inputTextElementForm.valuePlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
    ></ApplicationBuilderFormulaInputGroup>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.placeholder"
      :label="$t('inputTextElementForm.placeholderTitle')"
      :placeholder="$t('inputTextElementForm.placeholderPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
    ></ApplicationBuilderFormulaInputGroup>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('inputTextElementForm.requiredTitle') }}
      </label>
      <div class="control__elements">
        <Checkbox v-model="values.required"></Checkbox>
      </div>
    </FormElement>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import { DATA_PROVIDERS_ALLOWED_ELEMENTS } from '@baserow/modules/builder/enums'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup.vue'

export default {
  name: 'InputTextElementForm',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [form],
  data() {
    return {
      values: {
        default_value: '',
        required: false,
        placeholder: '',
      },
    }
  },
  computed: {
    DATA_PROVIDERS_ALLOWED_ELEMENTS: () => DATA_PROVIDERS_ALLOWED_ELEMENTS,
  },
  methods: {
    emitChange(newValues) {
      if (this.isFormValid()) {
        form.methods.emitChange.bind(this)(newValues)
      }
    },
  },
}
</script>
