<template>
  <form @submit.prevent="submit">
    <div class="control">
      <label class="control__label">
        <i class="fas fa-font"></i>
        {{ $t('applicationForm.nameLabel') }}
      </label>
      <div class="control__elements">
        <input
          ref="name"
          v-model="values.name"
          :class="{ 'input--error': $v.values.name.$error }"
          type="text"
          class="input input--large"
          @blur="$v.values.name.$touch()"
        />
        <div v-if="$v.values.name.$error" class="error">
          {{ $t('error.requiredField') }}
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
  name: 'ApplicationForm',
  mixins: [form],
  data() {
    return {
      values: {
        name: '',
      },
    }
  },
  mounted() {
    this.$refs.name.focus()
  },
  validations: {
    values: {
      name: { required },
    },
  },
}
</script>

<i18n>
{
  "en": {
    "applicationForm": {
      "nameLabel": "Name"
    }
  },
  "fr": {
    "applicationForm": {
      "nameLabel": "Nom"
    }
  }
}
</i18n>
