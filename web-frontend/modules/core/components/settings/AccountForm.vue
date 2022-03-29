<template>
  <form @submit.prevent="submit">
    <FormElement :error="fieldHasErrors('first_name')" class="control">
      <label class="control__label">
        {{ $t('accountForm.nameLabel') }}
      </label>
      <div class="control__elements">
        <input
          ref="name"
          v-model="values.first_name"
          :class="{ 'input--error': fieldHasErrors('first_name') }"
          type="text"
          class="input input--large"
          @blur="$v.values.first_name.$touch()"
        />
        <div v-if="fieldHasErrors('first_name')" class="error">
          {{ $t('error.requiredField') }}
        </div>
      </div>
    </FormElement>
    <FormElement class="control">
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
    </FormElement>
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
