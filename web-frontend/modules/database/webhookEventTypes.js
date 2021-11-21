import { Registerable } from '@baserow/modules/core/registry'

export class WebhookEventType extends Registerable {
  getName() {
    throw new Error('The name of an exporter type must be set.')
  }

  constructor(...args) {
    super(...args)
    this.type = this.getType()

    if (this.type === null) {
      throw new Error('The type name of an webhook event type must be set.')
    }
  }

  serialize() {
    return {
      type: this.type,
    }
  }

  /**
   * Should return an object containing an example of the webhook event type payload.
   */
  getExamplePayload(table, rowExample) {
    return {
      table_id: table.id,
      event_type: this.getType(),
      event_id: '00000000-0000-0000-0000-000000000000',
    }
  }
}

export class RowCreatedWebhookEventType extends WebhookEventType {
  getType() {
    return 'row.created'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('webhook.eventType.rowCreated')
  }

  getExamplePayload(table, rowExample) {
    const payload = super.getExamplePayload(table, rowExample)
    payload.row_id = rowExample.id
    payload.values = rowExample
    return payload
  }
}

export class RowUpdatedWebhookEventType extends WebhookEventType {
  getType() {
    return 'row.updated'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('webhook.eventType.rowUpdated')
  }

  getExamplePayload(table, rowExample) {
    const payload = super.getExamplePayload(table, rowExample)
    payload.row_id = rowExample.id
    payload.values = rowExample
    payload.old_values = rowExample
    return payload
  }
}

export class RowDeletedWebhookEventType extends WebhookEventType {
  getType() {
    return 'row.deleted'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('webhook.eventType.rowDeleted')
  }

  getExamplePayload(table, rowExample) {
    const payload = super.getExamplePayload(table, rowExample)
    payload.row_id = rowExample.id
    return payload
  }
}
