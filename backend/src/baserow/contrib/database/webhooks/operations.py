from baserow.contrib.database.table.operations import DatabaseTableOperationType


class ListTableWebhooksOperationType(DatabaseTableOperationType):
    type = "database.table.list_webhooks"


class CreateWebhookOperationType(DatabaseTableOperationType):
    type = "database.table.create_webhook"


class ReadWebhookOperationType(DatabaseTableOperationType):
    type = "database.table.webhook.read"


class UpdateWebhookOperationType(DatabaseTableOperationType):
    type = "database.table.webhook.update"


class TestTriggerWebhookOperationType(DatabaseTableOperationType):
    type = "database.table.webhook.test_trigger"


class DeleteWebhookOperationType(DatabaseTableOperationType):
    type = "database.table.webhook.delete"
