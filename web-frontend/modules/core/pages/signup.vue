<template>
  <div>
    <div class="box__head">
      <h1 class="box__head-title">
        {{ $t('signup.title') }}
      </h1>
      <LangPicker />
    </div>
    <template v-if="!settings.allow_new_signups">
      <div class="alert alert--simple alert--error alert--has-icon">
        <div class="alert__icon">
          <i class="fas fa-exclamation"></i>
        </div>
        <div class="alert__title">{{ $t('signup.disabled') }}</div>
        <p class="alert__content">
          {{ $t('signup.disabledMessage') }}
        </p>
      </div>
      <nuxt-link
        :to="{ name: 'login' }"
        class="button button--large button--primary"
      >
        <i class="fas fa-arrow-left"></i>
        {{ $t('action.backToLogin') }}
      </nuxt-link>
    </template>
    <AuthRegister v-else :invitation="invitation" @success="success">
      <ul class="action__links">
        <li>
          <nuxt-link :to="{ name: 'login' }">
            <i class="fas fa-arrow-left"></i>
            {{ $t('action.back') }}
          </nuxt-link>
        </li>
      </ul>
    </AuthRegister>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import groupInvitationToken from '@baserow/modules/core/mixins/groupInvitationToken'
import AuthRegister from '@baserow/modules/core/components/auth/AuthRegister'
import LangPicker from '@baserow/modules/core/components/LangPicker'

export default {
  components: { AuthRegister, LangPicker },
  mixins: [groupInvitationToken],
  layout: 'login',
  head() {
    return {
      title: 'Create new account',
    }
  },
  computed: {
    ...mapGetters({
      settings: 'settings/get',
    }),
  },
  methods: {
    success() {
      this.$nuxt.$router.push({ name: 'dashboard' })
    },
  },
}
</script>

<i18n>
{
  "en":{
    "signup": {
      "title": "Sign up",
      "disabled": "Sign up is disabled",
      "disabledMessage": "It's not possible to create an account because it has been disabled."
    }
  },
  "fr":{
    "signup": {
      "title": "Création de compte",
      "disabled": "Création de compte desactivée",
      "disabledMessage": "Vous ne pouvez pas créer de compte car la création de compte a été désactivée."
    }
  }
}
</i18n>
