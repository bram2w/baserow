import dataclasses
from typing import Optional

from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

from baserow.contrib.database.models import Database
from baserow.core.action.registries import ActionType, ActionTypeDescription
from baserow.core.action.scopes import GROUP_ACTION_CONTEXT, GroupActionScopeType
from baserow.core.models import Group
from baserow.core.utils import ChildProgressBuilder

from .handler import AirtableHandler


class ImportDatabaseFromAirtableActionType(ActionType):
    type = "import_database_from_airtable"
    description = ActionTypeDescription(
        _("Import database from Airtable"),
        _(
            'Imported database "%(installed_application_name)s" (%(installed_application_id)s) '
            'from Airtable share ID "%(airtable_share_id)s"'
        ),
        GROUP_ACTION_CONTEXT,
    )

    @dataclasses.dataclass
    class Params:
        airtable_share_id: str
        installed_application_id: int
        installed_application_name: str
        group_id: int
        group_name: str

    @classmethod
    def do(
        cls,
        user: AbstractUser,
        group: Group,
        airtable_share_id: str,
        progress_builder: Optional[ChildProgressBuilder] = None,
        **kwargs
    ) -> Database:
        """
        Imports a database from an Airtable share ID. The database will be
        created in the given group. The progress builder can be used to track
        the progress of the import.
        Look at .handler.AirtableHandler.import_from_airtable_to_group for more
        information.
        """

        database = AirtableHandler.import_from_airtable_to_group(
            group, airtable_share_id, progress_builder=progress_builder, **kwargs
        )

        params = cls.Params(
            airtable_share_id,
            database.id,
            database.name,
            group.id,
            group.name,
        )
        cls.register_action(user, params, cls.scope(group.id), group)

        return database

    @classmethod
    def scope(cls, group_id):
        return GroupActionScopeType.value(group_id)
