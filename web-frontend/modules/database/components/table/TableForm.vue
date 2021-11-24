<template>
  <form @submit.prevent="submit">
    <div class="control">
      <label class="control__label">
        <i class="fas fa-font"></i>
        {{ $t('tableForm.name') }}
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
  name: 'TableForm',
  mixins: [form],
  data() {
    return {
      values: {
        name: '',
      },
    }
  },
  validations: {
    values: {
      name: { required },
    },
  },
  mounted() {
    this.$refs.name.focus()
  },
}
</script>

<i18n>
{
  "en": {
    "tableForm": {
      "name": "Name"
    }
  },
  "fr": {
    "tableForm": {
      "name": "Nom"
    }
  }
}
</i18n>
