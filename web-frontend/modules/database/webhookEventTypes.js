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
  getExamplePayload(database, table, rowExample) {
    return {
      table_id: table.id,
      database_id: table.database_id,
      workspace_id: database.workspace.id,
      event_id: '00000000-0000-0000-0000-000000000000',
      event_type: this.getType(),
    }
  }
}

export class RowsCreatedWebhookEventType extends WebhookEventType {
  static getType() {
    return 'rows.created'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('webhook.eventType.rowsCreated')
  }

  getExamplePayload(database, table, rowExample) {
    const payload = super.getExamplePayload(database, table, rowExample)
    payload.items = [rowExample]
    return payload
  }
}

export class RowsUpdatedWebhookEventType extends WebhookEventType {
  static getType() {
    return 'rows.updated'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('webhook.eventType.rowsUpdated')
  }

  getExamplePayload(database, table, rowExample) {
    const payload = super.getExamplePayload(database, table, rowExample)
    payload.items = [rowExample]
    payload.old_items = [rowExample]
    return payload
  }
}

export class RowsDeletedWebhookEventType extends WebhookEventType {
  static getType() {
    return 'rows.deleted'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('webhook.eventType.rowsDeleted')
  }

  getExamplePayload(database, table, rowExample) {
    const payload = super.getExamplePayload(database, table, rowExample)
    payload.row_ids = [rowExample.id]
    return payload
  }
}
