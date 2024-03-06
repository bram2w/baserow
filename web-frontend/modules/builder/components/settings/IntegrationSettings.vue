<template>
  <div>
    <h2 class="box__title">{{ $t('integrationSettings.title') }}</h2>
    <div v-if="state === 'pending'" class="integration-settings__loader" />
    <template v-if="state === 'loaded'">
      <template v-if="integrations.length > 0">
        <p class="margin-top-3">
          {{ $t('integrationSettings.integrationMessage') }}
        </p>
        <div
          v-for="integration in integrations"
          :key="integration.id"
          class="integration_settings__integration"
        >
          <Presentation
            :image="getIntegrationType(integration).image"
            :title="integration.name"
            :subtitle="getIntegrationType(integration).getSummary(integration)"
            :rounded-icon="false"
            avatar-color="transparent"
            style="flex: 1"
          />
          <div class="integration_settings__integration-actions">
            <Button
              icon="iconoir-edit"
              type="light"
              @click="
                $refs[`IntegrationCreateEditModal_${integration.id}`][0].show()
              "
            />
            <Button
              icon="iconoir-trash"
              type="light"
              @click="deleteIntegration(integration)"
            />
          </div>
          <IntegrationCreateEditModal
            :ref="`IntegrationCreateEditModal_${integration.id}`"
            :data-integration-id="integration.id"
            :application="builder"
            :integration="integration"
          />
        </div>
      </template>
      <p v-else class="margin-top-3">
        {{ $t('integrationSettings.noIntegrationMessage') }}
      </p>
    </template>
  </div>
</template>

<script>
import IntegrationCreateEditModal from '@baserow/modules/core/components/integrations/IntegrationCreateEditModal'
import { mapActions, mapGetters } from 'vuex'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'IntegrationSettings',
  components: { IntegrationCreateEditModal },
  props: {
    builder: {
      type: Object,
      required: true,
    },
  },
  data() {
    return { state: null }
  },
  computed: {
    integrationTypes() {
      return this.$registry.getOrderedList('integration')
    },

    ...mapGetters({ integrations: 'integration/getIntegrations' }),
  },
  async mounted() {
    this.state = 'pending'
    try {
      await this.actionFetchIntegrations({ applicationId: this.builder.id })
    } catch (error) {
      notifyIf(error)
    }
    this.state = 'loaded'
  },
  methods: {
    ...mapActions({
      actionFetchIntegrations: 'integration/fetch',
      actionDeleteIntegration: 'integration/delete',
    }),
    getIntegrationType(integration) {
      return this.$registry.get('integration', integration.type)
    },
    async deleteIntegration(integration) {
      try {
        await this.actionDeleteIntegration({ integrationId: integration.id })
      } catch (error) {
        notifyIf(error)
      }
    },
  },
}
</script>
