from django.urls import reverse

import pytest
from pyinstrument import Profiler
from rest_framework.status import HTTP_200_OK

from baserow.contrib.database.application_types import DatabaseApplicationType
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import Field, TextField
from baserow.contrib.database.management.commands.fill_table_rows import fill_table_rows
from baserow.test_utils.helpers import setup_interesting_test_table


@pytest.mark.django_db
@pytest.mark.disabled_in_ci
# You must add --run-disabled-in-ci -s to pytest to run this test, you can do this in
# intellij by editing the run config for this test and adding --run-disabled-in-ci -s
# to additional args.
def test_speed_of_table_copy(data_fixture):
    # 2.2 seconds on AMD Ryzen 5900X, 32gb ram.
    text_field = data_fixture.create_text_field()

    count = 100
    fill_table_rows(count, text_field.table)

    profiler = Profiler()
    profiler.start()
    FieldHandler().copy_field(text_field)
    profiler.stop()
    print(profiler.output_text(unicode=True, color=True, show_all=True))


@pytest.mark.django_db
@pytest.mark.disabled_in_ci
# You must add --run-disabled-in-ci -s to pytest to run this test, you can do this in
# intellij by editing the run config for this test and adding --run-disabled-in-ci -s
# to additional args.
def test_speed_of_table_copy_via_export(data_fixture):
    # 8.84 seconds on AMD Ryzen 5900X, 32gb ram.
    text_field = data_fixture.create_text_field()

    count = 1000000
    fill_table_rows(count, text_field.table)

    profiler = Profiler()
    profiler.start()
    DatabaseApplicationType().export_serialized(text_field.table.database, None, None)
    profiler.stop()
    print(profiler.output_text(unicode=True, color=True, show_all=True))


@pytest.mark.django_db
@pytest.mark.disabled_in_ci
# You must add --run-disabled-in-ci -s to pytest to run this test, you can do this in
# intellij by editing the run config for this test and adding --run-disabled-in-ci -s
# to additional args.
def test_updating_many_fields_doesnt_slow_down_get_rows(data_fixture, api_client):
    table, user, row, _, context = setup_interesting_test_table(data_fixture)
    token = data_fixture.generate_token(user)
    count = 10000
    fill_table_rows(count, table)
    grid_view = data_fixture.create_grid_view(user=user, table=table)

    before_time, before_text = profile_get(api_client, grid_view, token)

    field_to_update_lots = TextField.objects.first()
    assert Field.trash.count() == 0
    num_updates = 40
    for i in range(num_updates):
        new_type = "file" if i % 2 == 0 else "number"
        url = reverse(
            "api:database:fields:item", kwargs={"field_id": field_to_update_lots.id}
        )
        response = api_client.patch(
            url,
            {"name": "field", "type": new_type},
            **{"HTTP_AUTHORIZATION": f"JWT {token}"},
        )
        assert response.status_code == HTTP_200_OK
    assert Field.trash.count() == num_updates

    after_time, after_text = profile_get(api_client, grid_view, token)

    print(f"BEFORE {before_time} AFTER {after_time}")
    assert before_time * 1.1 > after_time
    with open("before.txt", "w") as f:
        f.writelines(before_text)
    with open("after.txt", "w") as f:
        f.writelines(after_text)


def profile_get(api_client, grid_view, token):
    repeats = 10
    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid_view.id})
    limit = 200
    profiler = Profiler()
    profiler.start()
    for i in range(repeats):
        response = api_client.get(
            url, {"limit": limit}, **{"HTTP_AUTHORIZATION": f"JWT {token}"}
        )
        assert response.status_code == HTTP_200_OK
    session = profiler.stop()
    text = profiler.output_text(unicode=True, color=True, show_all=False)
    print(text)
    text = profiler.output_text(unicode=False, color=False, show_all=True)
    return session.cpu_time / repeats, text
