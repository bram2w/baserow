<template>
  <form @submit.prevent="submit">
    <h3>{{ $t('groupInviteForm.invitationFormTitle') }}</h3>
    <div class="row">
      <div class="col col-7">
        <div class="control">
          <div class="control__elements">
            <input
              ref="email"
              v-model="values.email"
              :class="{ 'input--error': $v.values.email.$error }"
              type="text"
              class="input"
              @blur="$v.values.email.$touch()"
            />
            <div v-if="$v.values.email.$error" class="error">
              {{ $t('groupInviteForm.errorInvalidEmail') }}
            </div>
          </div>
        </div>
      </div>
      <div class="col col-5">
        <div class="control">
          <div class="control__elements">
            <Dropdown v-model="values.permissions" :show-search="false">
              <DropdownItem
                :name="$t('permission.admin')"
                value="ADMIN"
                :description="$t('permission.adminDescription')"
              ></DropdownItem>
              <DropdownItem
                :name="$t('permission.member')"
                value="MEMBER"
                :description="$t('permission.memberDescription')"
              ></DropdownItem>
            </Dropdown>
          </div>
        </div>
      </div>
      <div class="col col-12">
        <div class="control">
          <div class="control__elements">
            <input
              ref="message"
              v-model="values.message"
              type="text"
              class="input"
              :placeholder="$t('groupInviteForm.optionalMessagePlaceholder')"
            />
          </div>
        </div>
      </div>
      <slot></slot>
    </div>
  </form>
</template>

<script>
import { required, email } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'GroupInviteForm',
  mixins: [form],
  data() {
    return {
      loading: false,
      values: {
        email: '',
        permissions: 'MEMBER',
        message: '',
      },
    }
  },
  validations: {
    values: {
      email: { required, email },
    },
  },
}
</script>

<i18n>
{
  "en": {
    "groupInviteForm": {
      "invitationFormTitle": "Invite by email",
      "optionalMessagePlaceholder": "Optional message",
      "errorInvalidEmail": "Please enter a valid e-mail address."
    }
  },
  "fr": {
    "groupInviteForm": {
      "invitationFormTitle": "Inviter par email",
      "optionalMessagePlaceholder": "Message optionnel",
      "errorInvalidEmail": "Veuillez saisir une adresse email valide."
    }
  }
}
</i18n>
