<template>
  <div class="premium-top-sidebar">
    <div v-if="impersonating" class="impersonate-warning">
      {{ $t('premiumTopSidebar.impersonateDescription') }}
      <div>
        <a
          :href="resolveAdminUsersHref()"
          class="button button--error button--tiny margin-top-1"
          :class="{ 'button--loading': loading }"
          @click="loading = true"
          >{{ $t('premiumTopSidebar.impersonateStop') }}</a
        >
      </div>
    </div>
    <div
      v-if="accountLevelPremium"
      v-tooltip="$t('premiumTopSidebar.premiumDescription')"
      class="user-level-premium"
    >
      {{ $t('premiumTopSidebar.premium') }}
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'PremiumTopSidebar',
  data() {
    return {
      loading: false,
    }
  },
  computed: {
    accountLevelPremium() {
      const validLicense = this.additionalUserData?.premium?.valid_license
      // The user has account level premium if the `valid_license` value is exactly
      // `true`. If it's an array, it means that it only has premium access for certain
      // groups.
      return validLicense === true
    },
    ...mapGetters({
      additionalUserData: 'auth/getAdditionalUserData',
      impersonating: 'impersonating/getImpersonating',
    }),
  },
  methods: {
    resolveAdminUsersHref() {
      const props = this.$nuxt.$router.resolve({ name: 'admin-users' })
      return props.href
    },
  },
}
</script>
