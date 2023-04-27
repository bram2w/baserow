from django.contrib.auth import get_user_model
from django.db import transaction

from baserow.contrib.builder.domains.models import Domain
from baserow.contrib.builder.elements.handler import ElementHandler
from baserow.contrib.builder.elements.registries import element_type_registry
from baserow.contrib.builder.models import Builder
from baserow.contrib.builder.pages.handler import PageHandler
from baserow.contrib.builder.pages.models import Page
from baserow.core.handler import CoreHandler

User = get_user_model()


@transaction.atomic
def load_test_data():
    print("Add builder basic data...")

    user = User.objects.get(email="admin@baserow.io")
    workspace = user.workspaceuser_set.get(workspace__name="Acme Corp").workspace

    try:
        builder = Builder.objects.get(
            name="Back to local website", workspace__isnull=False, trashed=False
        )
    except Builder.DoesNotExist:
        builder = CoreHandler().create_application(
            user, workspace, "builder", name="Back to local website"
        )

    Domain.objects.filter(domain_name="test1.getbaserow.io").delete()
    Domain.objects.create(builder=builder, domain_name="test1.getbaserow.io", order=1)

    try:
        homepage = Page.objects.get(name="Homepage", builder=builder)
    except Page.DoesNotExist:
        homepage = PageHandler().create_page(builder, "Homepage", "/")

        heading_element_type = element_type_registry.get("heading")
        paragraph_element_type = element_type_registry.get("paragraph")

        ElementHandler().create_element(
            heading_element_type, homepage, value="Back to local", level=1
        )
        ElementHandler().create_element(
            heading_element_type, homepage, value="Buy closer, Buy better", level=2
        )
        ElementHandler().create_element(
            paragraph_element_type,
            homepage,
            value=(
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit, "
                "sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
                "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
                "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in "
                "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
                "pariatur. Excepteur sint occaecat cupidatat non proident, "
                "sunt in culpa qui officia deserunt mollit anim id est laborum."
            ),
        )
        ElementHandler().create_element(
            heading_element_type,
            homepage,
            value="Give more sense to what you eat",
            level=2,
        )
        ElementHandler().create_element(
            paragraph_element_type,
            homepage,
            value=(
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit, "
                "sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
                "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
                "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in "
                "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
                "pariatur. Excepteur sint occaecat cupidatat non proident, "
                "sunt in culpa qui officia deserunt mollit anim id est laborum."
            ),
        )

    try:
        terms = Page.objects.get(name="Terms", builder=builder)
    except Page.DoesNotExist:
        terms = PageHandler().create_page(builder, "Terms", "/terms")

        heading_element_type = element_type_registry.get("heading")
        paragraph_element_type = element_type_registry.get("paragraph")

        ElementHandler().create_element(
            heading_element_type, terms, value="Terms", level=1
        )
        ElementHandler().create_element(
            heading_element_type, terms, value="Article 1. General", level=2
        )
        ElementHandler().create_element(
            paragraph_element_type,
            terms,
            value=(
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit, "
                "sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
                "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
                "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in "
                "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
                "pariatur. Excepteur sint occaecat cupidatat non proident, "
                "sunt in culpa qui officia deserunt mollit anim id est laborum."
            ),
        )
        ElementHandler().create_element(
            heading_element_type,
            terms,
            value="Article 2. Services",
            level=2,
        )
        ElementHandler().create_element(
            paragraph_element_type,
            terms,
            value=(
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit, "
                "sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
                "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
                "nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in "
                "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
                "pariatur. Excepteur sint occaecat cupidatat non proident, "
                "sunt in culpa qui officia deserunt mollit anim id est laborum."
            ),
        )
