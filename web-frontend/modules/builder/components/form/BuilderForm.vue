<template>
  <ApplicationForm
    :default-values="{ name: defaultName }"
    @submitted="$emit('submitted', $event)"
  >
    <FormElement class="builder-form__controls">
      <button
        class="button button--large"
        :class="{ 'button--loading': loading }"
        :disabled="loading"
        type="submit"
      >
        {{ $t('builderForm.submit') }}
      </button>
    </FormElement>
  </ApplicationForm>
</template>

<script>
import ApplicationForm from '@baserow/modules/core/components/application/ApplicationForm'
export default {
  name: 'BuilderForm',
  components: { ApplicationForm },
  props: {
    defaultName: {
      type: String,
      required: true,
    },
    loading: {
      type: Boolean,
      required: true,
    },
  },
}
</script>
