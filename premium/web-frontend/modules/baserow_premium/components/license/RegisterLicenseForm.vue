<template>
  <form @submit.prevent="submit">
    <div class="control">
      <label class="control__label">License key</label>
      <div class="control__elements">
        <textarea
          ref="license"
          v-model="values.license"
          :class="{ 'input--error': $v.values.license.$error }"
          type="text"
          class="input input--large textarea--modal"
          @blur="$v.values.license.$touch()"
        />
        <div v-if="$v.values.license.$error" class="error">
          This field is required.
        </div>
      </div>
    </div>
    <slot></slot>
  </form>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'RegisterLicenseForm',
  mixins: [form],
  data() {
    return {
      values: {
        license: '',
      },
    }
  },
  validations: {
    values: {
      license: { required },
    },
  },
  mounted() {
    this.$refs.license.focus()
  },
}
</script>
