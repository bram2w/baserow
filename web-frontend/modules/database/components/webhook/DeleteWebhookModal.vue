<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('deleteWebhookModal.title', { webhookName: webhook.name }) }}
    </h2>
    <Error :error="error"></Error>
    <div>
      <p>
        {{ $t('deleteWebhookModal.body') }}
      </p>
      <div class="actions">
        <div class="align-right">
          <a
            class="button button--large button--error"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
            @click="deleteWebhook()"
          >
            {{ $t('deleteWebhookModal.deleteButton') }}
          </a>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import WebhookService from '@baserow/modules/database/services/webhook'

export default {
  name: 'DeleteViewModal',
  mixins: [modal, error],
  props: {
    webhook: {
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
    async deleteWebhook() {
      this.loading = true

      try {
        await WebhookService(this.$client).delete(this.webhook.id)
        this.$emit('deleted', this.webhook)
      } catch (error) {
        this.handleError(error)
      }

      this.loading = false
    },
  },
}
</script>

<i18n>
{
  "en": {
    "deleteWebhookModal": {
      "title": "Delete {webhookName}",
      "deleteButton": "Delete webhook",
      "body": "Are you sure you want to delete this webhook? You will not be able to restore it later."
    }
  },
  "fr": {
    "deleteWebhookModal": {
      "title": "@TODO",
      "deleteButton": "@TODO",
      "body": "@TODO"
    }
  }
}
</i18n>
