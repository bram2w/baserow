<template>
  <div class="webhook__call" :class="{ 'webhook__call--open': isExpanded }">
    <div class="webhook__call-head">
      <div class="webhook__call-name">
        <div class="webhook__call-type">{{ call.event_type }}</div>
        <div class="webhook__call-target">
          {{ call.called_url }}
        </div>
      </div>
      <div class="webhook__call-description">
        <div class="webhook__call-info">{{ timestamp }}</div>
        <a class="webhook__call-toggle" @click="toggleExpand()">
          <div
            class="webhook__call-state"
            :class="{
              'webhook__head-call-state--ok': ok,
              'webhook__head-call-state--error': !ok,
            }"
          >
            {{ statusDescription }}
          </div>
          <i v-show="isExpanded" class="fas fa-chevron-up"></i>
          <i v-show="!isExpanded" class="fas fa-chevron-down"></i>
        </a>
      </div>
    </div>
    <div class="webhook__call-body">
      <div class="webhook__call-body-content">
        <div class="webhook__call-body-label">{{ $t('webhook.request') }}</div>
        <div
          class="webhook__code-container webhook__code-container--fixed-height"
        >
          <pre
            class="webhook__code webhook__code--small"
          ><code>{{ call.request }}</code></pre>
        </div>
      </div>
      <div class="webhook__call-body-content">
        <div class="webhook__call-body-label">{{ $t('webhook.response') }}</div>
        <div
          class="webhook__code-container webhook__code-container--fixed-height"
        >
          <pre
            class="webhook__code webhook__code--small"
          ><code>{{ call.response }}</code></pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import moment from '@baserow/modules/core/moment'

export default {
  name: 'WebhookCalls',
  props: {
    call: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      isExpanded: false,
    }
  },
  computed: {
    ok() {
      const status = this.call.response_status
      return status !== null && status >= 200 && status <= 299
    },
    timestamp() {
      return moment(this.call.called_time).format('YYYY-MM-DD HH:mm:ss')
    },
    statusDescription() {
      let description = ''
      if (this.call.response_status !== null) {
        description += this.call.response_status + ' '
      }

      description += this.ok
        ? this.$t('webhook.status.statusOK')
        : this.$t('webhook.status.statusNotOK')

      return description
    },
  },
  methods: {
    toggleExpand() {
      this.isExpanded = !this.isExpanded
    },
  },
}
</script>
