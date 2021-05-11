import pytest
from django.db.models import Q
from django.db.models.functions import Reverse, Upper

from baserow.contrib.database.fields.field_filters import (
    FilterBuilder,
    FILTER_TYPE_AND,
    FILTER_TYPE_OR,
    AnnotatedQ,
)


@pytest.mark.django_db
def test_building_filter_with_and_type_ands_all_provided_qs_together(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table, order=1, name="name")
    bool_field = data_fixture.create_boolean_field(
        table=table, order=2, name="is_active"
    )

    model = table.get_model()
    row_1 = model.objects.create(
        **{f"field_{text_field.id}": "name", f"field_{bool_field.id}": True}
    )
    model.objects.create(
        **{f"field_{text_field.id}": "name", f"field_{bool_field.id}": False}
    )

    builder = FilterBuilder(filter_type=FILTER_TYPE_AND)
    builder.filter(Q(**{f"field_{text_field.id}": "name"}))
    builder.filter(Q(**{f"field_{bool_field.id}": True}))

    queryset = builder.apply_to_queryset(model.objects)
    assert queryset.count() == 1
    assert row_1 in queryset


@pytest.mark.django_db
def test_building_filter_with_or_type_ors_all_provided_qs_together(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table, order=1, name="name")
    another_text_field = data_fixture.create_text_field(
        table=table, order=2, name="surname"
    )

    model = table.get_model()
    row_1 = model.objects.create(
        **{f"field_{text_field.id}": "name", f"field_{another_text_field.id}": "other"}
    )
    row_2 = model.objects.create(
        **{
            f"field_{text_field.id}": "not_name",
            f"field_{another_text_field.id}": "extra",
        }
    )
    model.objects.create(
        **{
            f"field_{text_field.id}": "not_name",
            f"field_{another_text_field.id}": "not_other",
        }
    )

    builder = FilterBuilder(filter_type=FILTER_TYPE_OR)
    builder.filter(Q(**{f"field_{text_field.id}": "name"}))
    builder.filter(Q(**{f"field_{another_text_field.id}": "extra"}))

    queryset = builder.apply_to_queryset(model.objects)
    assert queryset.count() == 2
    assert row_1 in queryset
    assert row_2 in queryset


@pytest.mark.django_db
def test_building_filter_with_annotated_qs_annotates_prior_to_filter(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table, order=1, name="name")
    another_text_field = data_fixture.create_text_field(
        table=table, order=2, name="surname"
    )

    model = table.get_model()
    row_1 = model.objects.create(
        **{f"field_{text_field.id}": "name", f"field_{another_text_field.id}": "other"}
    )
    model.objects.create(
        **{f"field_{text_field.id}": "eman", f"field_{another_text_field.id}": "extra"}
    )
    model.objects.create(
        **{
            f"field_{text_field.id}": "not_name",
            f"field_{another_text_field.id}": "not_other",
        }
    )

    builder = FilterBuilder(filter_type=FILTER_TYPE_OR)
    builder.filter(
        AnnotatedQ(
            annotation={"reversed_name": Reverse(f"field_{text_field.id}")},
            q={f"field_{text_field.id}": "name"},
        )
    )
    builder.filter(Q(**{f"reversed_name": "eman"}))

    queryset = builder.apply_to_queryset(model.objects)
    assert queryset.count() == 1
    assert row_1 in queryset


@pytest.mark.django_db
def test_building_filter_with_many_annotated_qs_merges_the_annotations(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table, order=1, name="name")
    another_text_field = data_fixture.create_text_field(
        table=table, order=2, name="surname"
    )

    model = table.get_model()
    row_1 = model.objects.create(
        **{f"field_{text_field.id}": "name", f"field_{another_text_field.id}": "other"}
    )
    model.objects.create(
        **{f"field_{text_field.id}": "eman", f"field_{another_text_field.id}": "extra"}
    )
    model.objects.create(
        **{
            f"field_{text_field.id}": "not_name",
            f"field_{another_text_field.id}": "not_other",
        }
    )

    builder = FilterBuilder(filter_type=FILTER_TYPE_AND)
    builder.filter(
        AnnotatedQ(
            annotation={"reversed_name": Reverse(f"field_{text_field.id}")},
            q={f"field_{text_field.id}": "name"},
        )
    )
    builder.filter(
        AnnotatedQ(
            annotation={"upper_name": Upper(f"field_{text_field.id}")},
            q={f"field_{text_field.id}": "name"},
        )
    )
    builder.filter(Q(reversed_name="eman"))
    builder.filter(Q(upper_name="NAME"))

    queryset = builder.apply_to_queryset(model.objects)
    assert queryset.count() == 1
    assert row_1 in queryset


@pytest.mark.django_db
def test_can_invert_an_annotated_q(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    text_field = data_fixture.create_text_field(table=table, order=1, name="name")
    another_text_field = data_fixture.create_text_field(
        table=table, order=2, name="surname"
    )

    model = table.get_model()
    model.objects.create(
        **{f"field_{text_field.id}": "name", f"field_{another_text_field.id}": "other"}
    )
    row_2 = model.objects.create(
        **{f"field_{text_field.id}": "eman", f"field_{another_text_field.id}": "extra"}
    )
    row_3 = model.objects.create(
        **{
            f"field_{text_field.id}": "not_name",
            f"field_{another_text_field.id}": "not_other",
        }
    )

    builder = FilterBuilder(filter_type=FILTER_TYPE_AND)
    q_to_invert = AnnotatedQ(
        annotation={"reversed_name": Reverse(f"field_{text_field.id}")},
        q={f"reversed_name": "eman"},
    )
    builder.filter(~q_to_invert)

    queryset = builder.apply_to_queryset(model.objects)
    assert queryset.count() == 2
    assert row_2 in queryset
    assert row_3 in queryset
