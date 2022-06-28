import pytest
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db.models import Value, CharField
from django.db.models.expressions import ExpressionWrapper
from django.db.models.functions import Concat
from django.test.utils import override_settings

from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import Field, TextField, LongTextField
from baserow.contrib.database.views.models import View
from baserow.core.db import LockedAtomicTransaction, specific_iterator
from baserow.core.models import Settings


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_locked_atomic_transaction(api_client, data_fixture):
    def is_locked(model):
        with connection.cursor() as cursor:
            table_name = model._meta.db_table
            cursor.execute(
                "select count(*) from pg_locks l join pg_class t on l.relation = "
                "t.oid WHERE relname = %(table_name)s;",
                {"table_name": table_name},
            )
            return cursor.fetchone()[0] > 0

    assert not is_locked(Settings)

    with LockedAtomicTransaction(Settings):
        assert is_locked(Settings)


@pytest.mark.django_db
def test_specific_iterator(data_fixture, django_assert_num_queries):
    text_field_1 = data_fixture.create_text_field()
    text_field_2 = data_fixture.create_text_field()
    text_field_3 = data_fixture.create_text_field()

    long_text_field_1 = data_fixture.create_long_text_field()
    long_text_field_2 = data_fixture.create_long_text_field()
    long_text_field_3 = data_fixture.create_long_text_field()

    base_queryset = Field.objects.filter(
        id__in=[
            text_field_1.id,
            text_field_2.id,
            text_field_3.id,
            long_text_field_1.id,
            long_text_field_2.id,
            long_text_field_3.id,
        ]
    ).order_by("id")

    with django_assert_num_queries(3):
        specific_objects = list(specific_iterator(base_queryset))

        assert isinstance(specific_objects[0], TextField)
        assert specific_objects[0].id == text_field_1.id

        assert isinstance(specific_objects[1], TextField)
        assert specific_objects[1].id == text_field_2.id

        assert isinstance(specific_objects[2], TextField)
        assert specific_objects[2].id == text_field_3.id

        assert isinstance(specific_objects[3], LongTextField)
        assert specific_objects[3].id == long_text_field_1.id

        assert isinstance(specific_objects[4], LongTextField)
        assert specific_objects[4].id == long_text_field_2.id

        assert isinstance(specific_objects[5], LongTextField)
        assert specific_objects[5].id == long_text_field_3.id


@pytest.mark.django_db
def test_specific_iterator_with_deleted_type(data_fixture, django_assert_num_queries):
    user = data_fixture.create_user()
    field_2 = data_fixture.create_text_field(user=user)

    # This field does not have a type, so we don't expect it to end up in the
    # specific objects.
    Field.objects.create(
        table=data_fixture.create_database_table(),
        order=1,
        name="Test",
        primary=False,
        content_type=field_2.content_type,
    )

    base_queryset = Field.objects.all()

    with pytest.raises(Field.DoesNotExist):
        list(specific_iterator(base_queryset))


@pytest.mark.django_db
def test_specific_iterator_with_trashed_objects(
    data_fixture, django_assert_num_queries
):
    user = data_fixture.create_user()
    field = data_fixture.create_text_field(user=user)
    FieldHandler().delete_field(user=user, field=field)

    base_queryset = Field.objects_and_trash.all()
    specific_objects = list(specific_iterator(base_queryset))
    assert len(specific_objects) == 1


@pytest.mark.django_db
def test_specific_iterator_respecting_order(data_fixture, django_assert_num_queries):
    text_field_1 = data_fixture.create_text_field()
    long_text_field_1 = data_fixture.create_long_text_field()

    base_queryset = Field.objects.filter(
        id__in=[
            text_field_1.id,
            long_text_field_1.id,
        ]
    ).order_by("-id")

    specific_objects = list(specific_iterator(base_queryset))
    assert specific_objects[0].id == long_text_field_1.id
    assert specific_objects[1].id == text_field_1.id


@pytest.mark.django_db
def test_specific_iterator_with_annotation(data_fixture, django_assert_num_queries):
    text_field_1 = data_fixture.create_text_field()
    text_field_2 = data_fixture.create_text_field()

    base_queryset = (
        Field.objects.filter(
            id__in=[
                text_field_1.id,
                text_field_2.id,
            ]
        )
        .annotate(
            tmp_test_annotation=ExpressionWrapper(
                Concat(Value("test"), "id"),
                output_field=CharField(),
            )
        )
        .order_by("id")
    )

    with django_assert_num_queries(2):
        specific_objects = list(specific_iterator(base_queryset))

    assert specific_objects[0].tmp_test_annotation == f"test{text_field_1.id}"
    assert specific_objects[1].tmp_test_annotation == f"test{text_field_2.id}"


@pytest.mark.django_db
def test_specific_iterator_with_select_related(data_fixture, django_assert_num_queries):
    grid_view = data_fixture.create_grid_view()
    gallery_view = data_fixture.create_gallery_view()
    data_fixture.create_view_filter(view=grid_view)
    data_fixture.create_view_filter(view=gallery_view)
    data_fixture.create_view_filter(view=gallery_view)

    base_queryset = View.objects.filter(
        id__in=[
            grid_view.id,
            gallery_view.id,
        ]
    ).select_related("content_type")

    with django_assert_num_queries(3):
        specific_objects = list(specific_iterator(base_queryset))
        assert isinstance(specific_objects[0].content_type, ContentType)
        assert isinstance(specific_objects[1].content_type, ContentType)


@pytest.mark.django_db
def test_specific_iterator_with_prefetch_related(
    data_fixture, django_assert_num_queries
):
    grid_view = data_fixture.create_grid_view()
    gallery_view = data_fixture.create_gallery_view()
    filter_1 = data_fixture.create_view_filter(view=grid_view)
    filter_2 = data_fixture.create_view_filter(view=gallery_view)
    filter_3 = data_fixture.create_view_filter(view=gallery_view)

    base_queryset = View.objects.filter(
        id__in=[
            grid_view.id,
            gallery_view.id,
        ]
    ).prefetch_related("viewfilter_set")

    with django_assert_num_queries(4):
        specific_objects = list(specific_iterator(base_queryset))
        all_1 = specific_objects[0].viewfilter_set.all()
        assert all_1[0].id == filter_1.id
        all_2 = specific_objects[1].viewfilter_set.all()
        assert all_2[0].id == filter_2.id
        assert all_2[1].id == filter_3.id
