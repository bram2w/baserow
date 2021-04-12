from .registries import FieldConverter
from .models import LinkRowField, FileField


class RecreateFieldConverter(FieldConverter):
    def alter_field(
        self,
        from_field,
        to_field,
        from_model,
        to_model,
        from_model_field,
        to_model_field,
        user,
        connection,
    ):
        """
        Does the field alteration by removing the old field and creating the new field.
        The success rate of this converter is very high, but the downside is that the
        data is lost.
        """

        with connection.schema_editor() as schema_editor:
            schema_editor.remove_field(from_model, from_model_field)
            schema_editor.add_field(to_model, to_model_field)


class LinkRowFieldConverter(RecreateFieldConverter):
    type = "link_row"

    def is_applicable(self, from_model, from_field, to_field):
        return (
            (
                isinstance(from_field, LinkRowField)
                and not isinstance(to_field, LinkRowField)
            )
            or (
                not isinstance(from_field, LinkRowField)
                and isinstance(to_field, LinkRowField)
            )
            or (
                # If both fields are LinkRowFields and neither the linked table nor the
                # multiple setting has changed.
                isinstance(from_field, LinkRowField)
                and isinstance(to_field, LinkRowField)
                and from_field.link_row_table_id != to_field.link_row_table_id
            )
        )


class FileFieldConverter(RecreateFieldConverter):
    type = "file"

    def is_applicable(self, from_model, from_field, to_field):
        return (
            isinstance(from_field, FileField) and not isinstance(to_field, FileField)
        ) or (not isinstance(from_field, FileField) and isinstance(to_field, FileField))
