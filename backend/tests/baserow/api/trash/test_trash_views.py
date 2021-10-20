import pytest
from django.shortcuts import reverse
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
)

from baserow.core.models import Group, TrashEntry, Application
from baserow.core.trash.handler import TrashHandler


@pytest.mark.django_db
def test_deleting_a_group_moves_it_to_the_trash_and_hides_it(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    group_to_delete = data_fixture.create_group(user=user)

    url = reverse("api:groups:item", kwargs={"group_id": group_to_delete.id})
    with freeze_time("2020-01-01 12:00"):
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT

    response = api_client.get(
        reverse("api:groups:list"),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )
    assert response.status_code == HTTP_200_OK
    assert response.json() == []

    response = api_client.get(
        reverse(
            "api:trash:contents",
            kwargs={
                "group_id": group_to_delete.id,
            },
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "application": None,
                "group": group_to_delete.id,
                "id": TrashEntry.objects.first().id,
                "parent_trash_item_id": None,
                "trash_item_id": group_to_delete.id,
                "trash_item_type": "group",
                "trashed_at": "2020-01-01T12:00:00Z",
                "user_who_trashed": user.first_name,
                "name": group_to_delete.name,
                "parent_name": None,
                "extra_description": None,
            }
        ],
    }


@pytest.mark.django_db
def test_can_restore_a_deleted_trash_item(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    group_to_delete = data_fixture.create_group(user=user)

    url = reverse("api:groups:item", kwargs={"group_id": group_to_delete.id})
    with freeze_time("2020-01-01 12:00"):
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT

    response = api_client.patch(
        reverse(
            "api:trash:restore",
        ),
        {
            "trash_item_type": "group",
            "trash_item_id": group_to_delete.id,
        },
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_204_NO_CONTENT

    assert Group.objects.count() == 1
    assert Group.trash.count() == 0

    response = api_client.get(
        reverse(
            "api:trash:contents",
            kwargs={
                "group_id": group_to_delete.id,
            },
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
    }


@pytest.mark.django_db
def test_cant_restore_a_deleted_trash_item_if_not_in_group(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    other_user, other_token = data_fixture.create_user_and_token()
    group_to_delete = data_fixture.create_group(user=user)

    url = reverse("api:groups:item", kwargs={"group_id": group_to_delete.id})
    with freeze_time("2020-01-01 12:00"):
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT

    response = api_client.patch(
        reverse(
            "api:trash:restore",
        ),
        {
            "trash_item_type": "group",
            "trash_item_id": group_to_delete.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {other_token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"


@pytest.mark.django_db
def test_cant_restore_a_non_existent_trashed_item(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    response = api_client.patch(
        reverse(
            "api:trash:restore",
        ),
        {
            "trash_item_type": "group",
            "trash_item_id": 99999,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TRASH_ITEM_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_cant_restore_a_trashed_item_with_a_missing_parent(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)
    application = data_fixture.create_database_application(user=user, group=group)
    table = data_fixture.create_database_table(user=user, database=application)
    model = table.get_model()
    row = model.objects.create()

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": row.id}
    )
    with freeze_time("2020-01-01 12:00"):
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT

    response = api_client.patch(
        reverse(
            "api:trash:restore",
        ),
        {
            "trash_item_type": "row",
            "parent_trash_item_id": 99999,
            "trash_item_id": row.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TRASH_ITEM_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_cant_restore_a_trash_item_marked_for_perm_deletion(
    api_client, data_fixture, settings
):
    user, token = data_fixture.create_user_and_token()
    group_to_delete = data_fixture.create_group(user=user)

    trashed_at = timezone.now()
    time_when_trash_item_old_enough = trashed_at + timezone.timedelta(
        hours=settings.HOURS_UNTIL_TRASH_PERMANENTLY_DELETED + 1
    )

    with freeze_time(trashed_at):
        url = reverse("api:groups:item", kwargs={"group_id": group_to_delete.id})
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT

    with freeze_time(time_when_trash_item_old_enough):
        TrashHandler.mark_old_trash_for_permanent_deletion()
        TrashHandler.permanently_delete_marked_trash()

    response = api_client.patch(
        reverse(
            "api:trash:restore",
        ),
        {
            "trash_item_type": "group",
            "trash_item_id": group_to_delete.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_TRASH_ITEM_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_can_get_trash_structure(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    group_to_delete = data_fixture.create_group()
    normal_group = data_fixture.create_group()
    data_fixture.create_user_group(user=user, group=group_to_delete, order=1)
    data_fixture.create_user_group(user=user, group=normal_group, order=2)
    # Another group for a different user which should not be displayed below
    data_fixture.create_group()
    application = data_fixture.create_database_application(
        user=user, group=group_to_delete
    )
    trashed_application = data_fixture.create_database_application(
        user=user, group=normal_group
    )

    url = reverse("api:groups:item", kwargs={"group_id": group_to_delete.id})
    with freeze_time("2020-01-01 12:00"):
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT

    url = reverse(
        "api:applications:item", kwargs={"application_id": trashed_application.id}
    )
    with freeze_time("2020-01-01 12:00"):
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT

    response = api_client.get(
        reverse(
            "api:trash:list",
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "groups": [
            {
                "id": group_to_delete.id,
                "trashed": True,
                "name": group_to_delete.name,
                "applications": [
                    {"id": application.id, "name": application.name, "trashed": False}
                ],
            },
            {
                "id": normal_group.id,
                "trashed": False,
                "name": normal_group.name,
                "applications": [
                    {
                        "id": trashed_application.id,
                        "name": trashed_application.name,
                        "trashed": True,
                    }
                ],
            },
        ]
    }


@pytest.mark.django_db
def test_getting_a_non_existent_group_returns_404(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    response = api_client.get(
        reverse(
            "api:trash:contents",
            kwargs={"group_id": 99999},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GROUP_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_getting_a_non_existent_app_returns_404(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)

    url = reverse(
        "api:trash:contents",
        kwargs={"group_id": group.id},
    )
    response = api_client.get(
        f"{url}?application_id=99999",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_APPLICATION_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_getting_a_app_for_diff_group_returns_400(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)
    other_group = data_fixture.create_group(user=user)

    app = data_fixture.create_database_application(user=user, group=other_group)

    url = reverse(
        "api:trash:contents",
        kwargs={"group_id": group.id},
    )
    response = api_client.get(
        f"{url}?application_id={app.id}",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_APPLICATION_NOT_IN_GROUP"


@pytest.mark.django_db
def test_user_cant_get_trash_contents_for_group_they_are_not_a_member_of(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    (
        other_unpermissioned_user,
        unpermissioned_token,
    ) = data_fixture.create_user_and_token()

    group_to_delete = data_fixture.create_group(user=user)

    url = reverse("api:groups:item", kwargs={"group_id": group_to_delete.id})
    with freeze_time("2020-01-01 12:00"):
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT

    url = reverse(
        "api:trash:contents",
        kwargs={
            "group_id": group_to_delete.id,
        },
    )
    response = api_client.get(
        url,
        HTTP_AUTHORIZATION=f"JWT {unpermissioned_token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"


@pytest.mark.django_db
def test_can_get_trash_contents_for_undeleted_group(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    group = data_fixture.create_group(user=user)

    url = reverse(
        "api:trash:contents",
        kwargs={
            "group_id": group.id,
        },
    )
    response = api_client.get(
        url,
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
    }


@pytest.mark.django_db
def test_can_get_trash_contents_for_undeleted_app(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    group = data_fixture.create_group(user=user)
    app = data_fixture.create_database_application(user=user, group=group)

    url = reverse(
        "api:trash:contents",
        kwargs={
            "group_id": group.id,
        },
    )
    response = api_client.get(
        f"{url}?application_id={app.id}",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
    }


@pytest.mark.django_db
def test_emptying_a_trashed_group_marks_it_for_perm_deletion(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    group_to_delete = data_fixture.create_group(user=user)

    url = reverse("api:groups:item", kwargs={"group_id": group_to_delete.id})
    with freeze_time("2020-01-01 12:00"):
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT

    url = reverse(
        "api:trash:contents",
        kwargs={
            "group_id": group_to_delete.id,
        },
    )
    response = api_client.delete(
        f"{url}",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_204_NO_CONTENT

    assert Group.objects.count() == 0
    assert Group.trash.count() == 1
    assert TrashEntry.objects.get(
        trash_item_id=group_to_delete.id
    ).should_be_permanently_deleted

    response = api_client.get(
        reverse(
            "api:trash:contents",
            kwargs={
                "group_id": group_to_delete.id,
            },
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GROUP_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_emptying_a_non_existent_group_returns_404(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()

    response = api_client.delete(
        reverse(
            "api:trash:contents",
            kwargs={"group_id": 99999},
        ),
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_GROUP_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_emptying_a_non_existent_app_returns_404(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)

    url = reverse(
        "api:trash:contents",
        kwargs={"group_id": group.id},
    )
    response = api_client.delete(
        f"{url}?application_id=99999",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_APPLICATION_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_emptying_a_app_for_diff_group_returns_400(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)
    other_group = data_fixture.create_group(user=user)

    app = data_fixture.create_database_application(user=user, group=other_group)

    url = reverse(
        "api:trash:contents",
        kwargs={"group_id": group.id},
    )
    response = api_client.delete(
        f"{url}?application_id={app.id}",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_APPLICATION_NOT_IN_GROUP"


@pytest.mark.django_db
def test_user_cant_empty_trash_contents_for_group_they_are_not_a_member_of(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    (
        other_unpermissioned_user,
        unpermissioned_token,
    ) = data_fixture.create_user_and_token()

    group_to_delete = data_fixture.create_group(user=user)

    url = reverse("api:groups:item", kwargs={"group_id": group_to_delete.id})
    with freeze_time("2020-01-01 12:00"):
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT

    url = reverse(
        "api:trash:contents",
        kwargs={
            "group_id": group_to_delete.id,
        },
    )
    response = api_client.delete(
        url,
        HTTP_AUTHORIZATION=f"JWT {unpermissioned_token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_USER_NOT_IN_GROUP"


@pytest.mark.django_db
def test_emptying_a_trashed_app_marks_it_for_perm_deletion(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)
    trashed_database = data_fixture.create_database_application(user=user, group=group)

    url = reverse(
        "api:applications:item", kwargs={"application_id": trashed_database.id}
    )
    with freeze_time("2020-01-01 12:00"):
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT

    url = reverse(
        "api:trash:contents",
        kwargs={
            "group_id": group.id,
        },
    )
    response = api_client.delete(
        f"{url}",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_204_NO_CONTENT

    assert Application.objects.count() == 0
    assert Application.trash.count() == 1
    assert TrashEntry.objects.get(
        trash_item_id=trashed_database.id
    ).should_be_permanently_deleted

    url = reverse(
        "api:trash:contents",
        kwargs={
            "group_id": group.id,
        },
    )
    response = api_client.get(
        f"{url}?application_id={trashed_database.id}",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_404_NOT_FOUND
    assert response.json()["error"] == "ERROR_APPLICATION_DOES_NOT_EXIST"


@pytest.mark.django_db
def test_deleting_a_user_who_trashed_something_returns_null_user_who_trashed(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    other_user, other_token = data_fixture.create_user_and_token()
    group_to_delete = data_fixture.create_group(user=user)
    data_fixture.create_user_group(user=other_user, group=group_to_delete)

    url = reverse("api:groups:item", kwargs={"group_id": group_to_delete.id})
    with freeze_time("2020-01-01 12:00"):
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT

    user.delete()

    response = api_client.get(
        reverse(
            "api:trash:contents",
            kwargs={
                "group_id": group_to_delete.id,
            },
        ),
        HTTP_AUTHORIZATION=f"JWT {other_token}",
    )

    assert response.status_code == HTTP_200_OK
    assert response.json() == {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "application": None,
                "group": group_to_delete.id,
                "id": TrashEntry.objects.first().id,
                "parent_trash_item_id": None,
                "trash_item_id": group_to_delete.id,
                "trash_item_type": "group",
                "trashed_at": "2020-01-01T12:00:00Z",
                "user_who_trashed": None,
                "name": group_to_delete.name,
                "parent_name": None,
                "extra_description": None,
            }
        ],
    }


@pytest.mark.django_db
def test_restoring_an_item_which_doesnt_need_parent_id_with_one_returns_error(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)
    application = data_fixture.create_database_application(user=user, group=group)

    url = reverse("api:applications:item", kwargs={"application_id": application.id})
    with freeze_time("2020-01-01 12:00"):
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT

    response = api_client.patch(
        reverse(
            "api:trash:restore",
        ),
        {
            "trash_item_type": "application",
            "parent_trash_item_id": 99999,
            "trash_item_id": application.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_PARENT_ID_MUST_NOT_BE_PROVIDED"


@pytest.mark.django_db
def test_cant_restore_a_trashed_item_requiring_a_parent_id_without_providing_it(
    api_client, data_fixture
):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)
    application = data_fixture.create_database_application(user=user, group=group)
    table = data_fixture.create_database_table(user=user, database=application)
    model = table.get_model()
    row = model.objects.create()

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": table.id, "row_id": row.id}
    )
    with freeze_time("2020-01-01 12:00"):
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_204_NO_CONTENT

    response = api_client.patch(
        reverse(
            "api:trash:restore",
        ),
        {
            "trash_item_type": "row",
            "trash_item_id": row.id,
        },
        format="json",
        HTTP_AUTHORIZATION=f"JWT {token}",
    )

    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_PARENT_ID_MUST_BE_PROVIDED"


@pytest.mark.django_db
def test_cant_delete_same_item_twice(api_client, data_fixture):
    user, token = data_fixture.create_user_and_token()
    group = data_fixture.create_group(user=user)
    database = data_fixture.create_database_application(user=user)
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(user=user)
    row_table, _, rows = data_fixture.build_table(
        user=user, columns=[("text", "text")], rows=["test"]
    )
    row = rows[0]

    url = reverse("api:groups:item", kwargs={"group_id": group.id})
    _assert_delete_called_twice_returns_correct_api_error(api_client, group, token, url)

    url = reverse("api:applications:item", kwargs={"application_id": database.id})
    _assert_delete_called_twice_returns_correct_api_error(
        api_client, database, token, url
    )
    url = reverse("api:database:tables:item", kwargs={"table_id": table.id})
    _assert_delete_called_twice_returns_correct_api_error(api_client, table, token, url)

    url = reverse("api:database:fields:item", kwargs={"field_id": field.id})
    _assert_delete_called_twice_returns_correct_api_error(
        api_client, field, token, url, response_code=HTTP_200_OK
    )

    url = reverse(
        "api:database:rows:item", kwargs={"table_id": row_table.id, "row_id": row.id}
    )
    _assert_delete_called_twice_returns_correct_api_error(api_client, row, token, url)


def _assert_delete_called_twice_returns_correct_api_error(
    api_client, deletable_item, token, url, response_code=HTTP_204_NO_CONTENT
):
    with freeze_time("2020-01-01 12:00"):
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == response_code
    # Fake two requests doing the deletion at once by manually unsetting the trashed
    # flag so we can attempt to trash again and hit the integrity error.
    deletable_item.trashed = False
    deletable_item.save()
    with freeze_time("2020-01-01 12:00"):
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"JWT {token}")
    assert response.status_code == HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "ERROR_CANNOT_DELETE_ALREADY_DELETED_ITEM"
