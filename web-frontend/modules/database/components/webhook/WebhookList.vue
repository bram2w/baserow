<template>
  <div class="webhook__list">
    <p v-if="webhooks.length === 0" class="margin-top-2">
      {{ $t('webhookList.noWebhooksMessage') }}
    </p>
    <Webhook
      v-for="webhook in webhooks"
      :key="webhook.id"
      :webhook="webhook"
      :table="table"
      @updated="$emit('updated', $event)"
      @deleted="$emit('deleted', $event)"
    />
  </div>
</template>

<script>
import Webhook from './Webhook.vue'

export default {
  name: 'WebhookList',
  components: {
    Webhook,
  },
  props: {
    table: {
      type: Object,
      required: true,
    },
    webhooks: {
      type: Array,
      required: true,
    },
  },
}
</script>

<i18n>
{
  "en": {
    "webhookList": {
      "noWebhooksMessage": "You have not created any webhooks yet. Webhooks can be used in order to inform 3rd party systems when a row in Baserow has been created, updated or deleted."
    }
  },
  "fr": {
    "webhookList": {
      "noWebhooksMessage": "@TODO"
    }
  }
}
</i18n>
