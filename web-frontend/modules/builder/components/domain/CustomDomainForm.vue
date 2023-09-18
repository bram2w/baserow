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
          {{ $t('domainForm.invalidDomain') }}
        </div>
        <div v-if="serverErrors.domain_name.code === 'unique'" class="error">
          {{ $t('domainForm.notUniqueDomain') }}
        </div>
      </template>
    </FormElement>
  </form>
</template>

<script>
import { required, maxLength } from 'vuelidate/lib/validators'
import domainForm from '@baserow/modules/builder/mixins/domainForm'

export default {
  name: 'CustomDomainForm',
  mixins: [domainForm],
  data() {
    return {
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
}
</script>
