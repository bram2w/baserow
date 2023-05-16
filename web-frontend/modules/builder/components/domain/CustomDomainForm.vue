<template>
  <form @submit.prevent="submit">
    <FormElement :error="fieldHasErrors('domain_name')" class="control">
      <label class="control__label">
        {{ $t('customDomainForm.domainNameLabel') }}
      </label>
      <input
        v-model="values.domain_name"
        type="text"
        class="input"
        :class="{
          'input--error':
            fieldHasErrors('domain_name') || serverErrors.domain_name,
        }"
        @input="serverErrors.domain_name = null"
        @blur="$v.values.domain_name.$touch()"
      />
      <div
        v-if="$v.values.domain_name.$dirty && !$v.values.domain_name.required"
        class="error"
      >
        {{ $t('error.requiredField') }}
      </div>
      <div
        v-if="$v.values.domain_name.$dirty && !$v.values.domain_name.maxLength"
        class="error"
      >
        {{ $t('error.maxLength', { max: 255 }) }}
      </div>
      <template v-if="serverErrors.domain_name">
        <div v-if="serverErrors.domain_name.code === 'invalid'" class="error">
          {{ $t('customDomainForm.invalidDomain') }}
        </div>
        <div v-if="serverErrors.domain_name.code === 'unique'" class="error">
          {{ $t('customDomainForm.notUniqueDomain') }}
        </div></template
      >
    </FormElement>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import { required, maxLength } from 'vuelidate/lib/validators'

export default {
  name: 'DomainForm',
  mixins: [form],
  data() {
    return {
      serverErrors: { domain_name: null },
      values: {
        domain_name: '',
      },
    }
  },
  validations() {
    return {
      values: {
        domain_name: {
          required,
          maxLength: maxLength(255),
        },
      },
    }
  },
  methods: {
    handleServerError(error) {
      if (error.handler.code !== 'ERROR_REQUEST_BODY_VALIDATION') return false

      this.serverErrors = Object.fromEntries(
        Object.entries(error.handler.detail || {}).map(([key, value]) => [
          key,
          value[0],
        ])
      )

      return true
    },
    hasError() {
      return !this.isFormValid() || this.serverErrors.domain_name !== null
    },
  },
}
</script>
