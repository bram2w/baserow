import pytest

from baserow.contrib.database.views.tasks import update_view_index


@pytest.mark.django_db
def test_update_view_index_ignore_missing_view():
    # no exception occurs
    update_view_index(999)
