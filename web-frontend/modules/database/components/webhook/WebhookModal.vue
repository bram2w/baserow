<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('webhookModal.title', { name: table.name }) }}
    </h2>
    <Error :error="error"></Error>
    <div v-if="loading" class="loading"></div>
    <template v-else-if="!error.visible">
      <div class="align-right">
        <a v-if="state === 'list'" class="button" @click="state = 'create'">
          {{ $t('webhookModal.createWebhook') }}
          <i class="fas fa-plus"></i>
        </a>
        <a v-if="state === 'create'" class="button" @click="state = 'list'">
          <i class="fas fa-arrow-left"></i>
          {{ $t('webhookModal.backToList') }}
        </a>
      </div>
      <WebhookList
        v-if="state === 'list'"
        :table="table"
        :webhooks="webhooks"
        @updated="updated"
        @deleted="deleted"
      />
      <CreateWebhook
        v-else-if="state === 'create'"
        :table="table"
        @created="created"
      />
    </template>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import WebhookList from '@baserow/modules/database/components/webhook/WebhookList'
import CreateWebhook from '@baserow/modules/database/components/webhook/CreateWebhook'
import WebhookService from '@baserow/modules/database/services/webhook'

export default {
  name: 'WebhookModal',
  components: {
    CreateWebhook,
    WebhookList,
  },
  mixins: [modal, error],
  props: {
    table: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      state: 'list',
      webhooks: [],
    }
  },
  methods: {
    show(...args) {
      this.getRootModal().show(...args)
      this.fetchInitial()
    },
    async fetchInitial() {
      this.loading = true

      try {
        const { data } = await WebhookService(this.$client).fetchAll(
          this.table.id
        )
        this.webhooks = data
      } catch (e) {
        this.handleError(e)
      }

      this.loading = false
    },
    created(webhook) {
      this.webhooks.push(webhook)
      this.state = 'list'
    },
    updated(webhook) {
      const index = this.webhooks.findIndex((w) => w.id === webhook.id)
      if (index > -1) {
        Object.assign(this.webhooks[index], webhook)
      }
    },
    deleted(webhook) {
      const index = this.webhooks.findIndex((w) => w.id === webhook.id)
      if (index > -1) {
        this.webhooks.splice(index, 1)
      }
    },
  },
}
</script>

<i18n>
{
  "en": {
    "webhookModal": {
      "title": "{name} webhooks",
      "createWebhook": "Create webhook",
      "backToList": "Back to list"
    }
  },
  "fr": {
    "webhookModal": {
      "title": "@TODO",
      "createWebhook": "@TODO",
      "backToList": "@TODO"
    }
  }
}
</i18n>
