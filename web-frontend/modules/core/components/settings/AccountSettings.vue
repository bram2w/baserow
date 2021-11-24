<template>
  <div>
    <h2 class="box__title">{{ $t('accountSettings.title') }}</h2>
    <Error :error="error"></Error>
    <div v-if="success" class="alert alert--success alert--has-icon">
      <div class="alert__icon">
        <i class="fas fa-check"></i>
      </div>
      <div class="alert__title">
        {{ $t('accountSettings.changedTitle') }}
      </div>
      <p class="alert__content">
        {{ $t('accountSettings.changedDescription') }}
      </p>
    </div>
    <AccountForm :default-values="user" @submitted="submitted">
      <div class="actions actions--right">
        <button
          :class="{ 'button--loading': loading }"
          class="button button--large"
          :disabled="loading"
        >
          {{ $t('accountSettings.submitButton') }}
        </button>
      </div>
    </AccountForm>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import error from '@baserow/modules/core/mixins/error'
import AccountForm from '@baserow/modules/core/components/settings/AccountForm'

export default {
  components: { AccountForm },
  mixins: [error],
  data() {
    return {
      loading: false,
      success: false,
    }
  },
  computed: {
    ...mapGetters({
      user: 'auth/getUserObject',
    }),
  },
  methods: {
    async submitted(values) {
      this.success = false
      this.loading = true
      this.hideError()

      try {
        const data = await this.$store.dispatch('auth/update', values)
        this.$i18n.setLocale(data.language)
        this.success = true
        this.loading = false
      } catch (error) {
        this.loading = false
        this.handleError(error)
      }
    },
  },
}
</script>

<i18n>
{
  "en": {
    "accountSettings": {
      "title": "Account",
      "changedTitle": "Changed",
      "changedDescription": "Your account information has been changed.",
      "submitButton": "Update account"
    }
  },
  "fr": {
    "accountSettings": {
      "title": "Informations personnelles",
      "changedTitle": "Mise à jour",
      "changedDescription": "Les informations de votre compte utilisateur ont été mises à jour.",
      "submitButton": "Modifier les informations"
    }
  }
}
</i18n>
