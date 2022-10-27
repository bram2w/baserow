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
      v-if="highestLicenseType"
      v-tooltip="highestLicenseType.getTopSidebarTooltip()"
      class="instance-wide-license"
    >
      {{ highestLicenseType.getName() }}
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
    ...mapGetters({
      impersonating: 'impersonating/getImpersonating',
    }),
    highestLicenseType() {
      return this.$highestLicenseType()
    },
  },
  methods: {
    resolveAdminUsersHref() {
      const props = this.$nuxt.$router.resolve({ name: 'admin-users' })
      return props.href
    },
  },
}
</script>
