<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormGroup
      :label="$t('iframeElementForm.sourceTypeLabel')"
      small-label
      required
      class="margin-bottom-2"
    >
      <RadioGroup
        v-model="values.source_type"
        :options="iframeSourceTypeOptions"
        type="button"
      >
      </RadioGroup>
    </FormGroup>

    <ApplicationBuilderFormulaInputGroup
      v-if="values.source_type === IFRAME_SOURCE_TYPES.URL"
      key="url"
      v-model="values.url"
      :label="$t('iframeElementForm.urlLabel')"
      :placeholder="$t('iframeElementForm.urlPlaceholder')"
      :help-text="$t('iframeElementForm.urlHelp')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
      class="margin-bottom-2"
    ></ApplicationBuilderFormulaInputGroup>

    <ApplicationBuilderFormulaInputGroup
      v-if="values.source_type === IFRAME_SOURCE_TYPES.EMBED"
      key="embed"
      v-model="values.embed"
      :label="$t('iframeElementForm.embedLabel')"
      :placeholder="$t('iframeElementForm.embedPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
      class="margin-bottom-2"
    ></ApplicationBuilderFormulaInputGroup>

    <FormGroup
      :label="$t('iframeElementForm.heightLabel')"
      small-label
      required
      :error-message="
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
    >
      <FormInput
        v-model="values.height"
        type="number"
        :placeholder="$t('iframeElementForm.heightPlaceholder')"
        :to-value="(value) => parseInt(value)"
      ></FormInput>
    </FormGroup>
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
    iframeSourceTypeOptions() {
      return [
        {
          label: this.$t('iframeElementForm.urlLabel'),
          value: IFRAME_SOURCE_TYPES.URL,
        },
        {
          label: this.$t('iframeElementForm.embedLabel'),
          value: IFRAME_SOURCE_TYPES.EMBED,
        },
      ]
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
