import dataclasses
import re

import pytest

from baserow.core.action.registries import ActionTypeDescription, action_type_registry


@pytest.mark.django_db
def test_action_type_description_is_correct(data_fixture, django_assert_num_queries):
    for action_type in action_type_registry.get_all():
        assert isinstance(action_type.description, ActionTypeDescription)

        descr = action_type.description

        # A list of fields that are present in the `Params` dataclass.
        dataclass_fields = [f.name for f in dataclasses.fields(action_type.Params)]

        # To ensure that we can have `workspace` values in the `Params`, but
        # `group` values in `action_type.description.long`, the code below will
        # convert the `workspace` values into `group` ones. This can be removed
        # when the audit log translation files are updated.
        compat_dataclass_fields = []
        group_compat_map = {  # GroupDeprecation
            "workspace_id": "group_id",
            "workspace_name": "group_name",
            "original_workspace_name": "original_group_name",
        }
        for dataclass_field in dataclass_fields:
            for workspace_field, group_compat_field in group_compat_map.items():
                if dataclass_field == workspace_field:
                    dataclass_field = group_compat_field
            compat_dataclass_fields.append(dataclass_field)

        # ensure all the variables in the description are present in the Params
        assert set(
            re.findall(r"%\((\w+)\)s", str(descr.long) + str(descr.context))
        ).issubset(set(compat_dataclass_fields)), descr

        # ensure the description is not ending with a dot if there is a context
        if descr.context:
            assert not descr.long.endswith(".")
