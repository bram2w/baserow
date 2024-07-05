<template>
  <form @submit.prevent="submit">
    <FormGroup
      small-label
      required
      :label="$t('customDomainForm.domainNameLabel')"
      :error="fieldHasErrors('domain_name') || serverErrors.domain_name"
    >
      <FormInput
        v-model="values.domain_name"
        size="large"
        :error="fieldHasErrors('domain_name') || serverErrors.domain_name"
        @input="serverErrors.domain_name = null"
        @blur="$v.values.domain_name.$touch()"
      />

      <template #error>
        <span
          v-if="$v.values.domain_name.$dirty && !$v.values.domain_name.required"
          >{{ $t('error.requiredField') }}</span
        >

        <span
          v-if="
            $v.values.domain_name.$dirty && !$v.values.domain_name.maxLength
          "
        >
          {{ $t('error.maxLength', { max: 255 }) }}
        </span>

        <div v-if="serverErrors.domain_name">
          <span v-if="serverErrors.domain_name.code === 'invalid'">
            {{ $t('domainForm.invalidDomain') }}
          </span>
          <span v-if="serverErrors.domain_name.code === 'unique'">
            {{ $t('domainForm.notUniqueDomain') }}
          </span>
        </div>
      </template>
    </FormGroup>
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
