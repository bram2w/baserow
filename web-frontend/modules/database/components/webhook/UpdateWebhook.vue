<template>
  <div>
    <Error :error="error" />
    <WebhookForm
      ref="form"
      :table="table"
      :default-values="webhook"
      @submitted="submit"
      @formchange="handleFormChange"
    >
      <div class="actions">
        <a
          class="button button--primary button--error"
          @click="$refs.deleteWebhookModal.show()"
        >
          {{ $t('action.delete') }}
        </a>
        <div class="align-right">
          <p v-if="saved" class="color-success">
            <strong>{{ $t('webhook.successfullyUpdated') }}</strong>
          </p>
          <button
            v-if="!saved"
            class="button button--primary"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
          >
            {{ $t('action.save') }}
          </button>
        </div>
      </div>
      <DeleteWebhookModal
        ref="deleteWebhookModal"
        :webhook="webhook"
        @deleted="$emit('deleted', $event)"
      />
    </WebhookForm>
  </div>
</template>

<script>
import error from '@baserow/modules/core/mixins/error'
import WebhookForm from '@baserow/modules/database/components/webhook/WebhookForm'
import DeleteWebhookModal from '@baserow/modules/database/components/webhook/DeleteWebhookModal'
import WebhookService from '@baserow/modules/database/services/webhook'

export default {
  name: 'UpdateWebhook',
  components: { WebhookForm, DeleteWebhookModal },
  mixins: [error],
  props: {
    table: {
      type: Object,
      required: true,
    },
    webhook: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      saved: false,
    }
  },
  methods: {
    handleFormChange() {
      this.saved = false
    },
    async submit(values) {
      this.hideError()
      this.loading = true

      try {
        const { data } = await WebhookService(this.$client).update(
          this.webhook.id,
          values
        )
        this.saved = true
        this.$emit('updated', data)

        setTimeout(() => {
          this.saved = false
        }, 5000)
      } catch (error) {
        this.handleError(error)
      }

      this.loading = false
    },
  },
}
</script>
