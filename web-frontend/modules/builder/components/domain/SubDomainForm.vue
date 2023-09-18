<template>
  <form @submit.prevent="submit">
    <FormElement :error="fieldHasErrors('domain_name')" class="control">
      <FormInput
        v-model="domainPrefix"
        :label="$t('subDomainForm.domainNameLabel')"
        :error="
          $v.values.domain_name.$dirty && !$v.values.domain_name.required
            ? $t('error.requiredField')
            : $v.values.domain_name.$dirty && !$v.values.domain_name.maxLength
            ? $t('error.maxLength', { max: 255 })
            : serverErrors.domain_name &&
              serverErrors.domain_name.code === 'invalid'
            ? $t('domainForm.invalidDomain')
            : serverErrors.domain_name &&
              serverErrors.domain_name.code === 'unique'
            ? $t('domainForm.notUniqueDomain')
            : ''
        "
        @input="serverErrors.domain_name = null"
      >
        <template #suffix> .{{ domain }} </template>
      </FormInput>
    </FormElement>
  </form>
</template>

<script>
import { maxLength, required } from 'vuelidate/lib/validators'
import domainForm from '@baserow/modules/builder/mixins/domainForm'

export default {
  name: 'SubDomainForm',
  mixins: [domainForm],
  data() {
    return {
      domainPrefix: '',
      values: {
        domain_name: '',
      },
    }
  },
  watch: {
    domainPrefix(value) {
      this.values.domain_name = `${value}.${this.domain}`
    },
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
