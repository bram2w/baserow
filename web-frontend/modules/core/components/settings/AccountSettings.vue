<template>
  <div>
    <h2 class="box__title">{{ $t('accountSettings.title') }}</h2>
    <Error :error="error"></Error>
    <Alert v-if="success" type="success">
      <template #title>{{ $t('accountSettings.changedTitle') }}</template>
      <p>{{ $t('accountSettings.changedDescription') }}</p>
    </Alert>
    <AccountForm :default-values="user" @submitted="submitted">
      <div class="actions actions--right">
        <Button
          type="primary"
          size="large"
          :loading="loading"
          :disabled="loading"
        >
          {{ $t('accountSettings.submitButton') }}
        </Button>
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
