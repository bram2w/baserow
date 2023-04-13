<template>
  <ExpandableCard :default-expanded="isOnlyDomain">
    <template #header="{ toggle, expanded }">
      <div class="domain-card__header">
        <div>
          <div class="margin-bottom-1 domain-card__name">
            {{ domain.domain_name }}
          </div>
          <a class="domain-card__detail-button-link" @click="toggle">
            {{ $t('domainCard.detailLabel')
            }}<i
              class="fas domain-card__detail-button-icon"
              :class="expanded ? 'fa-chevron-down' : 'fa-chevron-right'"
            />
          </a>
        </div>
        <div>
          <div class="margin-bottom-1">{{ domainType.name }}</div>
          <div class="domain-card__last-published">
            LAST PUBLISHED PLACEHOLDER
          </div>
        </div>
      </div>
    </template>
    <component
      :is="domainType.detailsComponent"
      :domain="domain"
      @delete="$emit('delete')"
    />
  </ExpandableCard>
</template>

<script>
import DnsStatus from '@baserow/modules/builder/components/domain/DnsStatus'
export default {
  name: 'DomainCard',
  components: { DnsStatus },
  props: {
    domain: {
      type: Object,
      required: true,
    },
    isOnlyDomain: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    domainType() {
      return this.$registry.get('domain', this.domain.type)
    },
  },
}
</script>
