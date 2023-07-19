<template>
  <form ref="form" @submit.prevent="submit">
    <FormInput
      v-model="values.name"
      :label="$t('integrationEditForm.name')"
      :placeholder="$t('integrationEditForm.namePlaceholder')"
      :error="
        $v.values.name.$dirty && !$v.values.name.required
          ? $t('error.requiredField')
          : !$v.values.name.maxLength
          ? $t('error.maxLength', { max: 255 })
          : ''
      "
      @blur="$v.values.name.$touch()"
    />
    <component
      :is="integrationType.formComponent"
      :application="application"
      :default-values="defaultValues"
    />
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import { required, maxLength } from 'vuelidate/lib/validators'

export default {
  mixins: [form],
  props: {
    application: {
      type: Object,
      required: true,
    },
    integrationType: {
      type: Object,
      required: true,
    },
  },
  data() {
    return { values: { name: '' }, allowedValues: ['name'] }
  },
  validations() {
    return {
      values: {
        name: {
          required,
          maxLength: maxLength(255),
        },
      },
    }
  },
}
</script>
