from django.contrib.auth import get_user_model

from baserow.contrib.builder.models import Builder
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.table.models import Table
from baserow.core.app_auth_providers.registries import app_auth_provider_type_registry
from baserow.core.integrations.models import Integration
from baserow.core.models import WorkspaceUser
from baserow.core.user.exceptions import UserAlreadyExist
from baserow.core.user.handler import UserHandler
from baserow.core.user_sources.handler import UserSourceHandler
from baserow.core.user_sources.registries import user_source_type_registry
from baserow_enterprise.integrations.local_baserow.models import (
    LocalBaserowPasswordAppAuthProvider,
    LocalBaserowUserSource,
)
from baserow_enterprise.role.default_roles import default_roles

User = get_user_model()


def load_test_data():
    # Get the user created in the main module
    user = User.objects.get(email="admin@baserow.io")
    workspace = user.workspaceuser_set.get(workspace__name="Acme Corp").workspace

    print("Add one user per existing role in the same workspace as admin")
    for i, r in enumerate(default_roles.keys()):
        rl = r.lower()
        try:
            user = UserHandler().create_user(rl, f"{rl}@baserow.io", "password")
        except UserAlreadyExist:
            user = User.objects.get(email=f"{rl}@baserow.io")

        WorkspaceUser.objects.update_or_create(
            workspace=workspace, user=user, defaults=dict(permissions=r, order=i + 1)
        )

    builder = Builder.objects.get(
        name="Back to local website", workspace__isnull=False, trashed=False
    )

    integration = Integration.objects.get(
        name="Local baserow", application__trashed=False, application_id=builder.id
    )

    user_table = Table.objects.get(
        name="User Accounts",
        database__workspace=workspace,
        database__trashed=False,
    )

    email_field = Field.objects.get(table=user_table, name="Email")
    username_field = Field.objects.get(table=user_table, name="Username")
    password_field = Field.objects.get(table=user_table, name="Password")

    user_source_type = user_source_type_registry.get("local_baserow")

    try:
        user_source = LocalBaserowUserSource.objects.get(
            name="Local baserow",
            application__trashed=False,
            application_id=builder.id,
        )
    except LocalBaserowUserSource.DoesNotExist:
        user_source = UserSourceHandler().create_user_source(
            user_source_type,
            builder,
            name="Local baserow",
            table=user_table,
            application_id=builder.id,
            integration=integration,
            email_field=email_field,
            name_field=username_field,
        )

    auth_provider_type = app_auth_provider_type_registry.get("local_baserow_password")

    try:
        LocalBaserowPasswordAppAuthProvider.objects.get(
            user_source_id=user_source.id,
        )
    except LocalBaserowPasswordAppAuthProvider.DoesNotExist:
        auth_provider_type.create(
            user_source=user_source, password_field=password_field, enabled=True
        )
