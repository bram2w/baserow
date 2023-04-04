from django.test.utils import override_settings

import pytest

from baserow.contrib.builder.domains.exceptions import (
    DomainDoesNotExist,
    DomainNotInBuilder,
    OnlyOneDomainAllowed,
)
from baserow.contrib.builder.domains.handler import DomainHandler
from baserow.contrib.builder.domains.models import Domain


@pytest.mark.django_db
def test_get_domain(data_fixture):
    domain = data_fixture.create_builder_domain()
    assert DomainHandler().get_domain(domain.id).id == domain.id


@pytest.mark.django_db
def test_get_domain_domain_does_not_exist(data_fixture):
    with pytest.raises(DomainDoesNotExist):
        DomainHandler().get_domain(9999)


@pytest.mark.django_db
def test_get_domain_base_queryset(data_fixture, django_assert_num_queries):
    domain = data_fixture.create_builder_domain()

    # Without selecting related
    domain = DomainHandler().get_domain(domain.id)
    with django_assert_num_queries(2):
        workspace = domain.builder.workspace

    # With selecting related
    base_queryset = Domain.objects.select_related("builder", "builder__workspace")
    domain = DomainHandler().get_domain(domain.id, base_queryset=base_queryset)
    with django_assert_num_queries(0):
        workspace = domain.builder.workspace


@pytest.mark.django_db
def test_create_domain(data_fixture):
    builder = data_fixture.create_builder_application()
    expected_order = Domain.get_last_order(builder)

    domain = DomainHandler().create_domain(builder, "test.com")

    assert domain.order == expected_order
    assert domain.domain_name == "test.com"


@pytest.mark.django_db
@override_settings(FEATURE_FLAGS=["BUILDER"])
def test_create_domain_only_one_domain_allowed(data_fixture):
    builder = data_fixture.create_builder_application()

    DomainHandler().create_domain(builder, "test.com")

    with pytest.raises(OnlyOneDomainAllowed):
        DomainHandler().create_domain(builder, "new.com")


@pytest.mark.django_db
def test_delete_domain(data_fixture):
    domain = data_fixture.create_builder_domain()

    DomainHandler().delete_domain(domain)

    assert Domain.objects.count() == 0


@pytest.mark.django_db
def test_update_domain(data_fixture):
    domain = data_fixture.create_builder_domain(domain_name="test.com")

    DomainHandler().update_domain(domain, domain_name="new.com")

    domain.refresh_from_db()

    assert domain.domain_name == "new.com"


@pytest.mark.django_db
def test_order_domains(data_fixture):
    builder = data_fixture.create_builder_application()
    domain_one = data_fixture.create_builder_domain(builder=builder, order=1)
    domain_two = data_fixture.create_builder_domain(builder=builder, order=2)

    assert DomainHandler().order_domains(builder, [domain_two.id, domain_one.id]) == [
        domain_two.id,
        domain_one.id,
    ]

    domain_one.refresh_from_db()
    domain_two.refresh_from_db()

    assert domain_one.order == 2
    assert domain_two.order == 1


@pytest.mark.django_db
def test_order_domains_domain_not_in_builder(data_fixture):
    builder = data_fixture.create_builder_application()
    domain_one = data_fixture.create_builder_domain(builder=builder, order=1)
    domain_two = data_fixture.create_builder_domain(builder=builder, order=2)

    base_qs = Domain.objects.filter(id=domain_two.id)

    with pytest.raises(DomainNotInBuilder):
        DomainHandler().order_domains(
            builder, [domain_two.id, domain_one.id], base_qs=base_qs
        )
