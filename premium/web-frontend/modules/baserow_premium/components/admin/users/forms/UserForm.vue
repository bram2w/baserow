<template>
  <form @submit.prevent="submit">
    <div class="control">
      <label class="control__label">{{ $t('userForm.fullName') }}</label>
      <div class="control__elements">
        <input
          ref="name"
          v-model="values.name"
          :class="{ 'input--error': $v.values.name.$error }"
          type="text"
          class="input input--large"
          :disabled="loading"
          @blur="$v.values.name.$touch()"
        />
        <div v-if="$v.values.name.$error" class="error">
          {{ $t('userForm.error.invalidName') }}
        </div>
      </div>
    </div>
    <label class="control__label">{{ $t('userForm.email') }}</label>
    <div class="control">
      <div class="control__elements">
        <input
          ref="email"
          v-model="values.username"
          :class="{ 'input--error': $v.values.username.$error }"
          type="text"
          class="input input--large"
          :disabled="loading"
          @blur="$v.values.username.$touch()"
        />
        <div v-show="$v.values.username.$error" class="error">
          {{ $t('userForm.error.invalidEmail') }}
        </div>
        <div v-show="values.username !== user.username" class="warning">
          {{ $t('userForm.warning.changeEmail') }}
        </div>
      </div>
    </div>
    <label class="control__label">{{ $t('userForm.isActive') }}</label>
    <div class="control">
      <div class="control__elements">
        <Checkbox v-model="values.is_active" :disabled="loading"></Checkbox>
      </div>
      <div v-show="!values.is_active" class="warning">
        {{ $t('userForm.warning.inactiveUser') }}
      </div>
    </div>
    <label class="control__label">{{ $t('premium.user.isStaff') }}</label>
    <div class="control">
      <div class="control__elements">
        <Checkbox v-model="values.is_staff" :disabled="loading"></Checkbox>
      </div>
      <div v-show="values.is_staff" class="warning">
        {{ $t('userForm.warning.userStaff') }}
      </div>
    </div>
    <div class="actions">
      <slot></slot>
      <div class="align-right">
        <button
          class="button button--large button--primary"
          :class="{ 'button--loading': loading }"
          :disabled="loading"
        >
          {{ $t('action.save') }}
        </button>
      </div>
    </div>
  </form>
</template>

<script>
import { email, maxLength, minLength, required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'UserForm',
  mixins: [form],
  props: {
    user: {
      type: Object,
      required: true,
    },
    loading: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      allowedValues: ['username', 'name', 'is_active', 'is_staff'],
      values: {
        username: '',
        name: '',
        is_active: '',
        is_staff: '',
      },
    }
  },
  validations: {
    values: {
      name: { required, minLength: minLength(2), maxLength: maxLength(150) },
      username: { required, email },
    },
  },
}
</script>

<i18n>
{
  "en": {
    "userForm": {
      "fullName": "Full name",
      "email": "Email",
      "isActive": "Is active",
      "warning": {
        "changeEmail":"Changing this users email address means when they sign in they must use the new email address to do so. This must be communicated with that user.",
        "inactiveUser": "When a user is marked as inactive they are prevented from signing in.",
        "userStaff": "Making the user staff gives them admin access to all users, all groups and the ability to revoke your own staff permissions."
      },
      "error": {
        "invalidName": "Please enter a valid full name, it must be longer than 2 letters and less than 150.",
        "invalidEmail": "Please enter a valid e-mail address."
      }
    }
  },
  "fr": {
    "userForm": {
      "fullName": "Nom complet",
      "email": "Adresse électronique",
      "isActive": "Est actif",
      "warning": {
        "changeEmail":"Si vous changez l'adresse électronique, l'utilisateur devra désormais utiliser celle-ci pour s'identifier. Ceci doit être signifié à l'utilisateur.",
        "inactiveUser": "Un utilisateur inactif n'est plus en mesure de s'identifier.",
        "userStaff": "Un collaborateur a accès à la liste des utilisateurs, des groupes et peut changer les permissions de tous les utilisateurs."
      },
      "error": {
        "invalidName": "Veuillez saisir un nom valide, il doit être composé de plus de 2 charactères et moins de 150.",
        "invalidEmail": "Veuillez saisir une adresse électronique valide."
      }
    }
  }
}
</i18n>
