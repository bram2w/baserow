<template>
  <span class="last-published-domain-date">
    {{ $t('lastPublishedDomainDate.lastPublished') }}
    {{ getHumanDate(domain.last_published) }}
  </span>
</template>

<script>
import moment from '@baserow/modules/core/moment'

export default {
  name: 'LastPublishedDomainDate',
  props: {
    domain: {
      type: Object,
      required: true,
    },
  },
  methods: {
    getHumanDate(date) {
      if (!date) {
        return this.$t('lastPublishedDomainDate.neverPublished')
      }
      return moment.utc(date).fromNow()
    },
  },
}
</script>
