<template>
  <div>
    <Error :error="error" />
    <WebhookForm ref="form" :table="table" @submitted="submit">
      <div class="actions">
        <div class="align-right">
          <button
            class="button button--primary"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
          >
            {{ $t('action.save') }}
          </button>
        </div>
      </div>
    </WebhookForm>
  </div>
</template>

<script>
import error from '@baserow/modules/core/mixins/error'
import { ResponseErrorMessage } from '@baserow/modules/core/plugins/clientHandler'
import WebhookForm from '@baserow/modules/database/components/webhook/WebhookForm'
import WebhookService from '@baserow/modules/database/services/webhook'

export default {
  name: 'CreateWebhook',
  components: { WebhookForm },
  mixins: [error],
  props: {
    table: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
    }
  },
  methods: {
    async submit(values) {
      this.loading = true

      try {
        const { data } = await WebhookService(this.$client).create(
          this.table.id,
          values
        )
        this.$emit('created', data)
      } catch (error) {
        this.handleError(error, 'webhook', {
          ERROR_TABLE_WEBHOOK_MAX_LIMIT_EXCEEDED: new ResponseErrorMessage(
            this.$t('createWebhook.errorTableWebhookMaxLimitExceededTitle'),
            this.$t(
              'createWebhook.errorTableWebhookMaxLimitExceededDescription'
            )
          ),
        })
      }

      this.loading = false
    },
  },
}
</script>

<i18n>
{
  "en": {
    "createWebhook": {
      "errorTableWebhookMaxLimitExceededTitle": "Max webhooks exceeded",
      "errorTableWebhookMaxLimitExceededDescription": "Can't create the webhook becuase the maximum amount of webhooks per table has been exceeded."
    }
  },
  "fr": {
    "createWebhook": {
      "errorTableWebhookMaxLimitExceededTitle": "@TODO",
      "errorTableWebhookMaxLimitExceededDescription": "@TODO"
    }
  }
}
</i18n>
