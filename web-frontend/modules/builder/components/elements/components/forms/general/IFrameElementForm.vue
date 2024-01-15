<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormGroup :label="$t('iframeElementForm.sourceTypeLabel')">
      <RadioButton
        v-model="values.source_type"
        :value="IFRAME_SOURCE_TYPES.URL"
      >
        {{ $t('iframeElementForm.urlLabel') }}
      </RadioButton>
      <RadioButton
        v-model="values.source_type"
        :value="IFRAME_SOURCE_TYPES.EMBED"
      >
        {{ $t('iframeElementForm.embedLabel') }}
      </RadioButton>
    </FormGroup>
    <ApplicationBuilderFormulaInputGroup
      v-if="values.source_type === IFRAME_SOURCE_TYPES.URL"
      key="url"
      v-model="values.url"
      :label="$t('iframeElementForm.urlLabel')"
      :placeholder="$t('iframeElementForm.urlPlaceholder')"
      :help-text="$t('iframeElementForm.urlHelp')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
    ></ApplicationBuilderFormulaInputGroup>
    <ApplicationBuilderFormulaInputGroup
      v-if="values.source_type === IFRAME_SOURCE_TYPES.EMBED"
      key="embed"
      v-model="values.embed"
      :label="$t('iframeElementForm.embedLabel')"
      :placeholder="$t('iframeElementForm.embedPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
    ></ApplicationBuilderFormulaInputGroup>
    <FormInput
      v-model="values.height"
      type="number"
      :label="$t('iframeElementForm.heightLabel')"
      :placeholder="$t('iframeElementForm.heightPlaceholder')"
      :to-value="(value) => parseInt(value)"
      :error="
        $v.values.height.$dirty && !$v.values.height.required
          ? $t('error.requiredField')
          : !$v.values.height.integer
          ? $t('error.integerField')
          : !$v.values.height.minValue
          ? $t('error.minValueField', { min: 1 })
          : !$v.values.height.maxValue
          ? $t('error.maxValueField', { max: 2000 })
          : ''
      "
    ></FormInput>
  </form>
</template>

<script>
import elementForm from '@baserow/modules/builder/mixins/elementForm'
import { IFRAME_SOURCE_TYPES } from '@baserow/modules/builder/enums'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup.vue'
import { required, integer, minValue, maxValue } from 'vuelidate/lib/validators'

export default {
  name: 'IFrameElementForm',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [elementForm],
  data() {
    return {
      values: {
        source_type: IFRAME_SOURCE_TYPES.URL,
        url: '',
        embed: '',
        height: 300,
      },
    }
  },
  computed: {
    IFRAME_SOURCE_TYPES() {
      return IFRAME_SOURCE_TYPES
    },
  },
  validations() {
    return {
      values: {
        height: {
          required,
          integer,
          minValue: minValue(1),
          maxValue: maxValue(2000),
        },
      },
    }
  },
}
</script>
