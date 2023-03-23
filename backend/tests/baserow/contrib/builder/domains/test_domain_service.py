from unittest.mock import patch

import pytest

from baserow.contrib.builder.domains.exceptions import DomainNotInBuilder
from baserow.contrib.builder.domains.models import Domain
from baserow.contrib.builder.domains.service import DomainService
from baserow.core.exceptions import UserNotInWorkspace


@patch("baserow.contrib.builder.domains.service.domain_created")
@pytest.mark.django_db
def test_domain_created_signal_sent(domain_created_mock, data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)

    domain = DomainService().create_domain(user, builder, "test")

    assert domain_created_mock.called_with(domain=domain, user=user)


@pytest.mark.django_db
def test_create_domain_user_not_in_workspace(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application()

    with pytest.raises(UserNotInWorkspace):
        DomainService().create_domain(user, builder, "test")


@patch("baserow.contrib.builder.domains.service.domain_deleted")
@pytest.mark.django_db
def test_domain_deleted_signal_sent(domain_deleted_mock, data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)
    domain = data_fixture.create_builder_domain(builder=builder)

    DomainService().delete_domain(user, domain)

    assert domain_deleted_mock.called_with(
        builder=builder, domain_id=domain.id, user=user
    )


@pytest.mark.django_db(transaction=True)
def test_delete_domain_user_not_in_workspace(data_fixture):
    user = data_fixture.create_user()
    user_unrelated = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)

    domain = DomainService().create_domain(user, builder, "test")

    with pytest.raises(UserNotInWorkspace):
        DomainService().delete_domain(user_unrelated, domain)

    assert Domain.objects.count() == 1


@pytest.mark.django_db
def test_get_domain_user_not_in_workspace(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application()
    domain = data_fixture.create_builder_domain(builder=builder)

    with pytest.raises(UserNotInWorkspace):
        DomainService().get_domain(user, domain.id)


@patch("baserow.contrib.builder.domains.service.domain_updated")
@pytest.mark.django_db
def test_domain_updated_signal_sent(domain_updated_mock, data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)
    domain = data_fixture.create_builder_domain(builder=builder)

    DomainService().update_domain(user, domain, domain_name="new.com")

    assert domain_updated_mock.called_with(domain=domain, user=user)


@pytest.mark.django_db
def test_update_domain_user_not_in_workspace(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application()
    domain = data_fixture.create_builder_domain(builder=builder)

    with pytest.raises(UserNotInWorkspace):
        DomainService().update_domain(user, domain, domain_name="test.com")


@pytest.mark.django_db
def test_update_domain_invalid_values(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)
    domain = data_fixture.create_builder_domain(builder=builder)

    domain_updated = DomainService().update_domain(user, domain, nonsense="hello")

    assert hasattr(domain_updated, "nonsense") is False


@patch("baserow.contrib.builder.domains.service.domains_reordered")
@pytest.mark.django_db
def test_domains_reordered_signal_sent(domains_reordered_mock, data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)
    domain_one = data_fixture.create_builder_domain(builder=builder, order=1)
    domain_two = data_fixture.create_builder_domain(builder=builder, order=2)

    full_order = DomainService().order_domains(
        user, builder, [domain_two.id, domain_one.id]
    )

    assert domains_reordered_mock.called_with(
        builder=builder, order=full_order, user=user
    )


@pytest.mark.django_db
def test_order_domains_user_not_in_workspace(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application()
    domain_one = data_fixture.create_builder_domain(builder=builder, order=1)
    domain_two = data_fixture.create_builder_domain(builder=builder, order=2)

    with pytest.raises(UserNotInWorkspace):
        DomainService().order_domains(user, builder, [domain_two.id, domain_one.id])


@pytest.mark.django_db
def test_order_domains_domain_not_in_builder(data_fixture):
    user = data_fixture.create_user()
    builder = data_fixture.create_builder_application(user=user)
    domain_one = data_fixture.create_builder_domain(builder=builder, order=1)
    domain_two = data_fixture.create_builder_domain(order=2)

    with pytest.raises(DomainNotInBuilder):
        DomainService().order_domains(user, builder, [domain_two.id, domain_one.id])
