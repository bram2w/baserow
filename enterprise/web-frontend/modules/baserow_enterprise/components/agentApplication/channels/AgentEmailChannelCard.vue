<template>
  <div>
    <Alert v-if="!channel.config.inbound_configured" type="warning">
      <p>{{ $t('agentChannels.emailUnavailable') }}</p>
    </Alert>
    <FormGroup
      small-label
      :label="$t('agentChannels.emailAddressLabel')"
      :helper-text="$t('agentChannels.emailAddressHelp')"
      class="margin-bottom-2"
    >
      <div class="agent-configuration__channel-url">
        <div class="agent-configuration__channel-url-box">
          {{ channel.config.address }}
        </div>
        <a
          class="agent-configuration__channel-url-copy"
          :title="$t('agentChannels.copyAddress')"
          @click="copyAddress"
        >
          <i class="iconoir-copy"></i>
          <Copied ref="copied"></Copied>
        </a>
      </div>
    </FormGroup>
    <FormGroup
      small-label
      :label="$t('agentChannels.localpartLabel')"
      :helper-text="$t('agentChannels.localpartHelp', { domain })"
      class="margin-bottom-2"
    >
      <FormInput
        v-model="draft.localpart"
        :disabled="!canUpdate"
        :placeholder="$t('agentChannels.localpartPlaceholder')"
        @input="onConfigChanged"
      ></FormInput>
    </FormGroup>
    <FormGroup
      small-label
      :label="$t('agentChannels.sendViaLabel')"
      :helper-text="
        channel.config.instance_smtp_available
          ? $t('agentChannels.sendViaHelp')
          : $t('agentChannels.sendViaNoInstanceSmtp')
      "
      class="margin-bottom-2"
    >
      <IntegrationDropdown
        :model-value="smtpIntegrationId"
        :application="application"
        :integrations="smtpIntegrations"
        :integration-type="smtpIntegrationType"
        :allow-editing="canUpdate"
        :disabled="!canUpdate"
        :placeholder="$t('agentChannels.sendViaInstance')"
        @update:model-value="onSmtpIntegrationChanged"
      />
    </FormGroup>
    <div class="agent-configuration__field-row margin-bottom-2">
      <FormGroup small-label :label="$t('agentChannels.fromNameLabel')">
        <FormInput
          v-model="draft.fromName"
          :disabled="!canUpdate"
          :placeholder="agentName"
          @input="onConfigChanged"
        ></FormInput>
      </FormGroup>
      <FormGroup
        v-if="smtpIntegrationId"
        small-label
        required
        :label="$t('agentChannels.fromEmailLabel')"
      >
        <FormInput
          v-model="draft.fromEmail"
          :disabled="!canUpdate"
          placeholder="support@company.com"
          @input="onConfigChanged"
        ></FormInput>
      </FormGroup>
    </div>
    <AgentEmailSharedFields
      :channel="channel"
      :can-update="canUpdate"
      :allowed-sender-domains="draft.allowedSenderDomains"
      @update:require-approval="
        updateChannel({ config: { require_approval: $event } })
      "
      @update:allowed-sender-domains="
        (value) => {
          draft.allowedSenderDomains = value
          onConfigChanged()
        }
      "
    />
    <div class="agent-configuration__hint">
      {{ $t('agentChannels.emailHint') }}
    </div>
  </div>
</template>

<script>
import agentChannelCard from '@baserow_enterprise/mixins/agentChannelCard'
import AgentEmailSharedFields from '@baserow_enterprise/components/agentApplication/channels/AgentEmailSharedFields'
import IntegrationDropdown from '@baserow/modules/core/components/integrations/IntegrationDropdown'
import { copyToClipboard } from '@baserow/modules/database/utils/clipboard'

export default {
  name: 'AgentEmailChannelCard',
  components: { AgentEmailSharedFields, IntegrationDropdown },
  mixins: [agentChannelCard],
  data() {
    return {
      // An SMTP server picked before there is a sender address; the backend
      // only takes the two together, so it's saved with the address.
      pendingSmtpIntegrationId: null,
    }
  },
  computed: {
    smtpIntegrationId() {
      return (
        this.pendingSmtpIntegrationId || this.channel.config.smtp_integration_id
      )
    },
    domain() {
      return (this.channel.config.address || '').split('@')[1] || ''
    },
    smtpIntegrationType() {
      return this.$registry.get('integration', 'smtp')
    },
    smtpIntegrations() {
      return this.$store.getters['integration/getIntegrations'](
        this.application
      ).filter((integration) => integration.type === 'smtp')
    },
  },
  watch: {
    'channel.config.smtp_integration_id'(value) {
      if (value === this.pendingSmtpIntegrationId) {
        this.pendingSmtpIntegrationId = null
      }
    },
  },
  methods: {
    draftConfigValues() {
      const values = {
        localpart: this.draft.localpart.trim().toLowerCase(),
        from_name: this.draft.fromName,
        from_email: this.draft.fromEmail.trim(),
        allowed_sender_domains: this.draft.allowedSenderDomains
          .split(',')
          .map((domain) => domain.trim().toLowerCase())
          .filter(Boolean),
      }
      if (this.pendingSmtpIntegrationId && values.from_email) {
        values.smtp_integration_id = this.pendingSmtpIntegrationId
      }
      return values
    },
    async onSmtpIntegrationChanged(integrationId) {
      const fromEmail = this.draft.fromEmail.trim()
      if (integrationId && !fromEmail) {
        this.pendingSmtpIntegrationId = integrationId
        return
      }
      this.pendingSmtpIntegrationId = null
      const config = { smtp_integration_id: integrationId || null }
      if (integrationId) {
        config.from_email = fromEmail
      }
      await this.updateChannel({ config })
    },
    copyAddress() {
      copyToClipboard(this.channel.config.address)
      this.$refs.copied?.show()
    },
  },
}
</script>
