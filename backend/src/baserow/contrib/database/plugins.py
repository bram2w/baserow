from datetime import date

from django.utils.translation import gettext as _, override

from baserow.core.handler import CoreHandler
from baserow.core.registries import Plugin

from .table.handler import TableHandler
from .views.handler import ViewHandler
from .views.view_types import GridViewType
from .fields.handler import FieldHandler
from .fields.field_types import (
    TextFieldType,
    LongTextFieldType,
    BooleanFieldType,
    DateFieldType,
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
        view_handler = ViewHandler()
        field_handler = FieldHandler()

        with override(user.profile.language):
            database = core_handler.create_application(
                user,
                group,
                type_name=self.type,
                name=_("%(first_name)s's company") % {"first_name": user.first_name},
            )

        # Creating the example customers table.
        table = table_handler.create_table(user, database, name="Customers")
        customers_view = view_handler.create_view(
            user, table, GridViewType.type, name="Grid"
        )
        field_handler.create_field(user, table, TextFieldType.type, name="Last name")
        notes_field = field_handler.create_field(
            user, table, LongTextFieldType.type, name="Notes"
        )
        active_field = field_handler.create_field(
            user, table, BooleanFieldType.type, name="Active"
        )

        view_handler.update_field_options(
            user,
            customers_view,
            {notes_field.id: {"width": 400}, active_field.id: {"width": 100}},
            fields=[notes_field, active_field],
        )
        model = table.get_model(attribute_names=True)
        model.objects.create(name="Elon", last_name="Musk", active=True, order=1)
        model.objects.create(
            name="Bill",
            last_name="Gates",
            notes=(
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce "
                "dignissim, urna eget rutrum sollicitudin, sapien diam interdum nisi, "
                "quis malesuada nibh eros a est."
            ),
            active=False,
            order=2,
        )
        model.objects.create(name="Mark", last_name="Zuckerburg", active=True, order=3)
        model.objects.create(name="Jeffrey", last_name="Bezos", active=True, order=4)

        # Creating the example projects table.
        table_2 = table_handler.create_table(user, database, name="Projects")
        projects_view = view_handler.create_view(
            user, table_2, GridViewType.type, name="Grid"
        )
        field_handler.create_field(user, table_2, DateFieldType.type, name="Started")
        active_field = field_handler.create_field(
            user, table_2, BooleanFieldType.type, name="Active"
        )
        model = table_2.get_model(attribute_names=True)
        model.objects.create(
            name="Tesla", active=True, started=date(2020, 6, 1), order=1
        )
        model.objects.create(name="SpaceX", active=False, order=2)
        model.objects.create(
            name="Amazon", active=False, started=date(2018, 1, 1), order=3
        )
        view_handler.update_field_options(
            user,
            projects_view,
            {active_field.id: {"width": 100}},
            fields=[active_field],
        )
