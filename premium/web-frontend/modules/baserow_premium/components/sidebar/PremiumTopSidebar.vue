<template>
  <div class="premium-top-sidebar">
    <div v-if="impersonating" class="impersonate-warning">
      {{ $t('premiumTopSidebar.impersonateDescription') }}
      <div>
        <Button
          class="margin-top-1"
          type="danger"
          tag="a"
          size="small"
          :href="resolveAdminUsersHref()"
          :loading="loading"
          :disabled="loading"
          @click="loading = true"
          >{{ $t('premiumTopSidebar.impersonateStop') }}</Button
        >
      </div>
    </div>

    <Badge
      v-if="
        highestLicenseType && highestLicenseType.showInTopSidebarWhenActive()
      "
      v-tooltip="highestLicenseType.getTopSidebarTooltip()"
      :color="highestLicenseType.getLicenseBadgeColor()"
      class="instance-wide-license"
      bold
    >
      {{ highestLicenseType.getName() }}</Badge
    >
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
