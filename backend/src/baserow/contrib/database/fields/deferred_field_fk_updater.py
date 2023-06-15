import typing
from collections import defaultdict
from typing import Dict

if typing.TYPE_CHECKING:
    from baserow.contrib.database.fields.models import Field


class DeferredFieldFkUpdater:
    """
    This class keeps track of fields which have FKs to other fields which need to
    be set once we have bulk created a set of fields.

    For example, when importing a table/database/workspace we have to go through and
    create many fields all at once. Fields can have FKs to other fields, but because we
    can only create fields one a time we can't set these FKs to other fields as
    they might not exist yet.

    This class keeps track of which field instances have FKs which need to be set
    once all fields have been created in the database. At which point you can
    call `run_deferred_fk_updates` with a mapping from the original field ids to
    the new ones to bulk setup all the pending FKs.
    """

    def __init__(self):
        self.deferred_field_fk_updates_per_model_class = defaultdict(list)

    def add_deferred_fk_to_update(
        self, field: "Field", field_fk_attr: str, original_field_fk_id: int
    ):
        self.deferred_field_fk_updates_per_model_class[type(field)].append(
            (field, field_fk_attr, original_field_fk_id)
        )

    def run_deferred_fk_updates(self, original_to_new_field_id_mapping: Dict[int, int]):
        for (
            field_model_class,
            deferred_field_fk_updates,
        ) in self.deferred_field_fk_updates_per_model_class.items():
            fields_to_bulk_update = {}
            attr_names = set()
            for field, attr_name, desired_field_id in deferred_field_fk_updates:
                if desired_field_id:
                    field_to_bulk_update = fields_to_bulk_update.setdefault(
                        field.id, field
                    )
                    attr_names.add(attr_name)
                    setattr(
                        field_to_bulk_update,
                        attr_name,
                        original_to_new_field_id_mapping[desired_field_id],
                    )
            field_model_class.objects.bulk_update(
                fields_to_bulk_update.values(), attr_names
            )
