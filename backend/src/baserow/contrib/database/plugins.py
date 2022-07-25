from datetime import date

from django.utils.translation import gettext as _, override

from baserow.core.handler import CoreHandler
from baserow.core.registries import Plugin

from .table.handler import TableHandler
from baserow.contrib.database.rows.handler import RowHandler


LOREM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce "
    "dignissim, urna eget rutrum sollicitudin, sapien diam interdum nisi, "
    "quis malesuada nibh eros a est."
)


class DatabasePlugin(Plugin):
    type = "database"

    def user_created(self, user, group, group_invitation, template):
        """
        This method is called when a new user is created. We are going to create a
        database, table, view, fields and some rows here as an example for the user.
        """

        # If the user created an account in combination with a group invitation we
        # don't want to create the initial data in the group because data should
        # already exist.
        if group_invitation or template:
            return

        core_handler = CoreHandler()
        table_handler = TableHandler()
        row_handler = RowHandler()

        with override(user.profile.language):
            database = core_handler.create_application(
                user,
                group,
                type_name=self.type,
                name=_("%(first_name)s's company") % {"first_name": user.first_name},
            )

            # Creating the example customers table.
            table = table_handler.create_table_and_fields(
                user,
                database,
                name=_("Customers"),
                fields=[
                    (_("Name"), "text", {}),
                    (_("Last name"), "text", {}),
                    (_("Notes"), "long_text", {"field_options": {"width": 400}}),
                    (_("Active"), "boolean", {"field_options": {"width": 100}}),
                ],
            )

            data = [
                ["Ada", "Lovelace", "", True],
                ["Alan", "Turing", LOREM, False],
                ["Grace", "Hopper", "", True],
                ["John", "Von Neumann", "", True],
                ["Blaise", "Pascal", "", True],
            ]
            row_handler.import_rows(user, table, data, send_signal=False)

            # Creating the example projects table.
            table = table_handler.create_table_and_fields(
                user,
                database,
                name=_("Projects"),
                fields=[
                    (_("Name"), "text", {}),
                    (_("Started"), "date", {}),
                    (_("Active"), "boolean", {"field_options": {"width": 100}}),
                ],
            )

            data = [
                [_("Calculator"), str(date(1642, 1, 1)), False],
                [_("Turing machine"), str(date(1936, 6, 1)), True],
                [_("Computer architecture"), str(date(1945, 1, 1)), False],
                [_("Cellular Automata"), str(date(1952, 6, 1)), False],
            ]
            row_handler.import_rows(user, table, data, send_signal=False)
