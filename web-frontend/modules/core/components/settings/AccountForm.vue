<template>
  <form @submit.prevent="submit">
    <div class="control">
      <label class="control__label">
        {{ $t('accountForm.nameLabel') }}
      </label>
      <div class="control__elements">
        <input
          ref="name"
          v-model="values.first_name"
          :class="{ 'input--error': $v.values.first_name.$error }"
          type="text"
          class="input input--large"
          @blur="$v.values.first_name.$touch()"
        />
        <div v-if="$v.values.first_name.$error" class="error">
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </div>
    <div v-if="$env.ENABLE_I18N" class="control">
      <label class="control__label">
        <i class="fas fa-globe"></i> {{ $t('accountForm.languageLabel') }}
      </label>
      <div class="control__elements">
        <Dropdown v-model="values.language" :show-search="false">
          <DropdownItem
            v-for="locale in $i18n.locales"
            :key="locale.code"
            :name="locale.name"
            :value="locale.code"
          ></DropdownItem>
        </Dropdown>
      </div>
    </div>
    <slot></slot>
  </form>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'AccountForm',
  mixins: [form],
  data() {
    return {
      allowedValues: ['first_name', 'language'],
      values: {
        first_name: '',
        language: '',
      },
    }
  },
  validations: {
    values: {
      first_name: { required },
    },
  },
}
</script>

<i18n>
{
  "en": {
    "accountForm": {
      "nameLabel": "Your name",
      "languageLabel": "Interface language"
    }
  },
  "fr": {
    "accountForm": {
      "nameLabel": "Votre nom",
      "languageLabel": "Langue de l'interface"
    }
  }
}
</i18n>
