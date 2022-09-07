from django.core.exceptions import ValidationError

import pytest

from baserow.contrib.database.webhooks.models import TableWebhookHeader


@pytest.mark.django_db(transaction=True)
def test_header_validation(data_fixture):
    webhook = data_fixture.create_table_webhook()

    with pytest.raises(ValidationError):
        header = TableWebhookHeader(webhook=webhook, name="Test:", value="Test")
        header.full_clean()

    with pytest.raises(ValidationError):
        header = TableWebhookHeader(webhook=webhook, name="Test", value="\t\n\ntest")
        header.full_clean()
