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
        <tr class="dns-status__table-row">
          <td class="dns-status__table-cell">A</td>
          <td class="dns-status__table-cell">@</td>
          <td class="dns-status__table-cell">127.0.01</td>
          <td class="dns-status__table-cell">
            <i class="iconoir-warning-triangle color--deep-dark-orange" />
          </td>
        </tr>
        <tr class="dns-status__table-row">
          <td class="dns-status__table-cell">CNAME</td>
          <td class="dns-status__table-cell">www</td>
          <td class="dns-status__table-cell">{{ domain.domain_name }}</td>
          <td class="dns-status__table-cell">
            <i class="iconoir-check color--deep-dark-green" />
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
}
</script>
