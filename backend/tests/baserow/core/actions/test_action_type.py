import dataclasses
import re

import pytest

from baserow.core.action.registries import ActionTypeDescription, action_type_registry


@pytest.mark.django_db
def test_action_type_description_is_correct(data_fixture, django_assert_num_queries):
    for action_type in action_type_registry.get_all():
        assert isinstance(action_type.description, ActionTypeDescription)

        descr = action_type.description

        # ensure all the variables in the description are present in the Params
        assert set(
            re.findall(r"%\((\w+)\)s", str(descr.long) + str(descr.context))
        ).issubset(set([f.name for f in dataclasses.fields(action_type.Params)])), descr

        # ensure the description is not ending with a dot if there is a context
        if descr.context:
            assert not descr.long.endswith(".")
