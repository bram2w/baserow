<template>
  <div>
    <h1>{{ $t('inviteStep.title') }}</h1>
    <p>{{ $t('inviteStep.description') }}</p>
    <FormInput
      v-for="(email, i) in emails"
      :key="i"
      v-model="emails[i]"
      :label="i === 0 ? $t('inviteStep.collaboratorsLabel') : null"
      :placeholder="'example@gmail.com'"
      :error="
        $v.emails.$each[i].$dirty && !$v.emails.$each[i].email
          ? $t('error.email')
          : null
      "
      icon-right="iconoir-mail"
      @input="updateValue(i, $event)"
      @blur="$v.emails.$each[i].$touch()"
    />
  </div>
</template>

<script>
import { email } from 'vuelidate/lib/validators'

export default {
  name: 'InviteStep',
  data() {
    return {
      emails: ['', '', '', '', ''],
    }
  },
  mounted() {
    this.updateValue()
  },
  methods: {
    isValid() {
      return !this.$v.$invalid
    },
    updateValue() {
      const emails = this.emails.filter((email) => !!email)
      this.$emit('update-data', { emails })
    },
  },
  validations() {
    return {
      emails: {
        $each: { email },
      },
    }
  },
}
</script>
