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

export class RowsCreatedWebhookEventType extends WebhookEventType {
  getType() {
    return 'rows.created'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('webhook.eventType.rowsCreated')
  }

  getExamplePayload(table, rowExample) {
    const payload = super.getExamplePayload(table, rowExample)
    payload.items = [rowExample]
    return payload
  }
}

export class RowsUpdatedWebhookEventType extends WebhookEventType {
  getType() {
    return 'rows.updated'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('webhook.eventType.rowsUpdated')
  }

  getExamplePayload(table, rowExample) {
    const payload = super.getExamplePayload(table, rowExample)
    payload.items = [rowExample]
    payload.old_items = [rowExample]
    return payload
  }
}

export class RowsDeletedWebhookEventType extends WebhookEventType {
  getType() {
    return 'rows.deleted'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('webhook.eventType.rowsDeleted')
  }

  getExamplePayload(table, rowExample) {
    const payload = super.getExamplePayload(table, rowExample)
    payload.row_ids = [rowExample.id]
    return payload
  }
}
