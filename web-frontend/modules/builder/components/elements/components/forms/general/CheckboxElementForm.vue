<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.label"
      class="margin-bottom-2"
      small-label
      required
      :label="$t('checkboxElementForm.labelTitle')"
      :placeholder="$t('generalForm.labelPlaceholder')"
      :data-providers-allowed="dataProvidersAllowed"
    ></ApplicationBuilderFormulaInputGroup>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.default_value"
      class="margin-bottom-2"
      small-label
      required
      :label="$t('checkboxElementForm.valueTitle')"
      :placeholder="$t('generalForm.valuePlaceholder')"
      :data-providers-allowed="dataProvidersAllowed"
    ></ApplicationBuilderFormulaInputGroup>
    <FormGroup
      small-label
      required
      :label="$t('checkboxElementForm.requiredTitle')"
    >
      <Checkbox v-model="values.required"></Checkbox>
    </FormGroup>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup.vue'
import {
  CurrentRecordDataProviderType,
  DataSourceContextDataProviderType,
  DataSourceDataProviderType,
  PageParameterDataProviderType,
} from '@baserow/modules/builder/dataProviderTypes'

export default {
  name: 'CheckboxElementForm',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [form],
  data() {
    return {
      values: {
        label: '',
        default_value: '',
        required: false,
      },
    }
  },
  computed: {
    dataProvidersAllowed() {
      return [
        CurrentRecordDataProviderType.getType(),
        PageParameterDataProviderType.getType(),
        DataSourceDataProviderType.getType(),
        DataSourceContextDataProviderType.getType(),
      ]
    },
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
