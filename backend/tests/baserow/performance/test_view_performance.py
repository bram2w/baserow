from django.urls import reverse

import pytest
from pyinstrument import Profiler
from rest_framework.status import HTTP_200_OK

from baserow.contrib.database.management.commands.fill_table_rows import fill_table_rows
from baserow.test_utils.helpers import setup_interesting_test_table


@pytest.mark.django_db
@pytest.mark.disabled_in_ci
# You must add --run-disabled-in-ci -s to pytest to run this test, you can do this in
# intellij by editing the run config for this test and adding --run-disabled-in-ci -s
# to additional args.
def test_getting_rows_from_large_grid_view(data_fixture, api_client):
    table, user, row, _, context = setup_interesting_test_table(data_fixture)
    token = data_fixture.generate_token(user)
    count = 10000
    fill_table_rows(count, table)
    grid_view = data_fixture.create_grid_view(user=user, table=table)

    limit = 200
    profiler = Profiler()
    profiler.start()
    url = reverse("api:database:views:grid:list", kwargs={"view_id": grid_view.id})
    response = api_client.get(
        url, {"limit": limit}, **{"HTTP_AUTHORIZATION": f"JWT {token}"}
    )
    response_json = response.json()
    assert response.status_code == HTTP_200_OK
    assert response_json["count"] == count + 2
    assert len(response_json["results"]) == limit
    profiler.stop()
    print(profiler.output_text(unicode=True, color=True))
