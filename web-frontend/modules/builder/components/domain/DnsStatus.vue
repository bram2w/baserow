<template>
  <div>
    <div class="margin-bottom-1">
      {{ $t('dnsStatus.description') }}
    </div>
    <table class="dns-status__table">
      <thead class="dns-status__table-head">
        <td class="dns-status__table-cell">
          {{ $t('dnsStatus.typeHeader') }}
        </td>
        <td class="dns-status__table-cell">
          {{ $t('dnsStatus.hostHeader') }}
        </td>
        <td class="dns-status__table-cell">
          {{ $t('dnsStatus.valueHeader') }}
        </td>
        <td class="dns-status__table-cell" />
      </thead>
      <tbody>
        <tr v-if="isRootDomain" class="dns-status__table-row">
          <td class="dns-status__table-cell">ALIAS</td>
          <td class="dns-status__table-cell">{{ domain.domain_name }}</td>
          <td class="dns-status__table-cell">{{ webFrontendHostname }}.</td>
          <td class="dns-status__table-cell">
            <!--
            <i class="iconoir-warning-triangle color--deep-dark-orange" />
            -->
          </td>
        </tr>
        <tr v-else class="dns-status__table-row">
          <td class="dns-status__table-cell">CNAME</td>
          <td class="dns-status__table-cell">{{ domain.domain_name }}</td>
          <td class="dns-status__table-cell">{{ webFrontendHostname }}</td>
          <td class="dns-status__table-cell">
            <!--
            <i class="iconoir-warning-triangle color--deep-dark-orange" />
            -->
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
  name: 'DnsStatus',
  props: {
    domain: {
      type: Object,
      required: true,
    },
  },
  computed: {
    isRootDomain() {
      return this.domain.domain_name.split('.').length === 2
    },
    webFrontendHostname() {
      const url = new URL(this.$config.PUBLIC_WEB_FRONTEND_URL)
      return url.hostname
    },
  },
}
</script>
