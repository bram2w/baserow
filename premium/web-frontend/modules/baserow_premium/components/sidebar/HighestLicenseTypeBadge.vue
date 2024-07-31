<template>
  <Badge
    v-if="highestLicenseType && highestLicenseType.showInTopSidebarWhenActive()"
    v-tooltip="highestLicenseType.getTopSidebarTooltip()"
    :color="highestLicenseType.getLicenseBadgeColor()"
    bold
  >
    {{ highestLicenseType.getName() }}</Badge
  >
</template>

<script>
export default {
  name: 'HighestLicenseTypeBadge',
  computed: {
    highestLicenseType() {
      return this.$highestLicenseType()
    },
  },
}
</script>
