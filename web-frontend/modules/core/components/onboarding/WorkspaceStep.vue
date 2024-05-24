<template>
  <div>
    <h1>{{ $t('workspaceStep.title') }}</h1>
    <FormInput
      v-model="name"
      :placeholder="$t('workspaceStep.workspaceLabel') + '...'"
      :label="$t('workspaceStep.workspaceLabel')"
      large
      :error="
        $v.name.$dirty && !$v.name.required ? $t('error.requiredField') : null
      "
      @input="updateValue"
      @blur="$v.name.$touch()"
    />
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

export default {
  name: 'WorkspaceStep',
  data() {
    return {
      name: this.$store.getters['auth/getName'] + "'s workspace",
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
      this.$v.name.$touch()
      this.$emit('update-data', { name: this.name })
    },
  },
  validations() {
    return {
      name: { required },
    }
  },
}
</script>
