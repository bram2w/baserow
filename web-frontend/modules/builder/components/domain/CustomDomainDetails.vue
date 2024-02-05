<template>
  <div class="custom-domain-details">
    <DnsStatus :domain="domain" />
    <div class="actions actions--right">
      <a
        class="button button--error"
        :class="{ 'button--loading': domain._.loading }"
        @click="$emit('delete')"
      >
        {{ $t('action.delete') }}
      </a>
    </div>
  </div>
</template>

<script>
import DnsStatus from '@baserow/modules/builder/components/domain/DnsStatus'
export default {
  name: 'CustomDomainDetails',
  components: { DnsStatus },
  props: {
    domain: {
      type: Object,
      required: true,
    },
  },
}
</script>
