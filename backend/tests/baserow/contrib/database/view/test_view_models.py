import pytest

from baserow.contrib.database.views.models import (
    FormViewFieldOptions,
    GalleryViewFieldOptions,
    GridViewFieldOptions,
    ViewDecoration,
    ViewFilter,
    ViewSort,
)


@pytest.mark.django_db
def test_view_get_field_options(data_fixture):
    table = data_fixture.create_database_table()
    table_2 = data_fixture.create_database_table()
    data_fixture.create_text_field(table=table_2)
    field_1 = data_fixture.create_text_field(table=table)
    field_2 = data_fixture.create_text_field(table=table)
    grid_view = data_fixture.create_grid_view(table=table)
    form_view = data_fixture.create_form_view(table=table)

    field_options = grid_view.get_field_options()
    assert len(field_options) == 2
    assert field_options[0].field_id == field_1.id
    assert field_options[0].width == 200
    assert field_options[0].order == 32767
    assert field_options[1].field_id == field_2.id
    assert field_options[1].width == 200
    assert field_options[1].order == 32767

    field_3 = data_fixture.create_text_field(table=table)

    field_options = grid_view.get_field_options()
    assert len(field_options) == 2

    field_options = grid_view.get_field_options(create_if_missing=True)
    assert len(field_options) == 3
    assert field_options[0].field_id == field_1.id
    assert field_options[1].field_id == field_2.id
    assert field_options[2].field_id == field_3.id

    field_options = grid_view.get_field_options(create_if_missing=False)
    assert len(field_options) == 3
    assert field_options[0].field_id == field_1.id
    assert field_options[1].field_id == field_2.id
    assert field_options[2].field_id == field_3.id

    field_options = form_view.get_field_options(create_if_missing=False)
    assert len(field_options) == 2
    assert field_options[0].field_id == field_1.id
    assert field_options[0].name == ""
    assert field_options[0].description == ""
    assert field_options[1].field_id == field_2.id

    field_options = form_view.get_field_options(create_if_missing=True)
    assert len(field_options) == 3
    assert field_options[0].field_id == field_1.id
    assert field_options[1].field_id == field_2.id
    assert field_options[2].field_id == field_3.id


@pytest.mark.django_db
def test_rotate_view_slug(data_fixture):
    form_view = data_fixture.create_form_view()
    old_slug = str(form_view.slug)
    form_view.rotate_slug()
    assert str(form_view.slug) != old_slug


@pytest.mark.django_db
def test_view_filter_manager_view_trashed(data_fixture):
    grid_view = data_fixture.create_grid_view()
    data_fixture.create_view_filter(view=grid_view)

    assert ViewFilter.objects.count() == 1

    grid_view.trashed = True
    grid_view.save()

    assert ViewFilter.objects.count() == 0


@pytest.mark.django_db
def test_view_filter_manager_field_trashed(data_fixture):
    grid_view = data_fixture.create_grid_view()
    field = data_fixture.create_text_field(table=grid_view.table)
    data_fixture.create_view_filter(view=grid_view, field=field)

    assert ViewFilter.objects.count() == 1

    field.trashed = True
    field.save()

    assert ViewFilter.objects.count() == 0


@pytest.mark.django_db
def test_view_sort_manager_view_trashed(data_fixture):
    grid_view = data_fixture.create_grid_view()
    data_fixture.create_view_sort(view=grid_view)

    assert ViewSort.objects.count() == 1

    grid_view.trashed = True
    grid_view.save()

    assert ViewSort.objects.count() == 0


@pytest.mark.django_db
def test_view_sort_manager_field_trashed(data_fixture):
    grid_view = data_fixture.create_grid_view()
    field = data_fixture.create_text_field(table=grid_view.table)
    data_fixture.create_view_sort(view=grid_view, field=field)

    assert ViewSort.objects.count() == 1

    field.trashed = True
    field.save()

    assert ViewSort.objects.count() == 0


@pytest.mark.django_db
def test_grid_view_field_options_manager_view_trashed(data_fixture):
    grid_view = data_fixture.create_grid_view()
    field = data_fixture.create_text_field(table=grid_view.table)
    data_fixture.create_grid_view_field_option(grid_view, field)

    assert GridViewFieldOptions.objects.count() == 1

    grid_view.trashed = True
    grid_view.save()

    assert GridViewFieldOptions.objects.count() == 0


@pytest.mark.django_db
def test_grid_view_field_options_manager_field_trashed(data_fixture):
    grid_view = data_fixture.create_grid_view()
    field = data_fixture.create_text_field(table=grid_view.table)
    data_fixture.create_grid_view_field_option(grid_view, field)

    assert GridViewFieldOptions.objects.count() == 1

    field.trashed = True
    field.save()

    assert GridViewFieldOptions.objects.count() == 0


@pytest.mark.django_db
def test_gallery_view_field_options_manager_view_trashed(data_fixture):
    gallery_view = data_fixture.create_gallery_view()
    field = data_fixture.create_text_field(table=gallery_view.table)
    data_fixture.create_gallery_view_field_option(gallery_view, field)

    assert GalleryViewFieldOptions.objects.count() == 1

    gallery_view.trashed = True
    gallery_view.save()

    assert GalleryViewFieldOptions.objects.count() == 0


@pytest.mark.django_db
def test_gallery_view_field_options_manager_field_trashed(data_fixture):
    gallery_view = data_fixture.create_gallery_view()
    field = data_fixture.create_text_field(table=gallery_view.table)
    data_fixture.create_gallery_view_field_option(gallery_view, field)

    assert GalleryViewFieldOptions.objects.count() == 1

    field.trashed = True
    field.save()

    assert GalleryViewFieldOptions.objects.count() == 0


@pytest.mark.django_db
def test_form_view_field_options_manager_view_trashed(data_fixture):
    form_view = data_fixture.create_form_view()
    field = data_fixture.create_text_field(table=form_view.table)
    data_fixture.create_form_view_field_option(form_view, field)

    assert FormViewFieldOptions.objects.count() == 1

    form_view.trashed = True
    form_view.save()

    assert FormViewFieldOptions.objects.count() == 0


@pytest.mark.django_db
def test_form_view_field_options_manager_field_trashed(data_fixture):
    form_view = data_fixture.create_form_view()
    field = data_fixture.create_text_field(table=form_view.table)
    data_fixture.create_form_view_field_option(form_view, field)

    assert FormViewFieldOptions.objects.count() == 1

    field.trashed = True
    field.save()

    assert FormViewFieldOptions.objects.count() == 0


@pytest.mark.django_db
def test_view_decoration_manager_view_trashed(data_fixture):
    view = data_fixture.create_grid_view()
    data_fixture.create_view_decoration(view=view)

    assert ViewDecoration.objects.count() == 1

    view.trashed = True
    view.save()

    assert ViewDecoration.objects.count() == 0


@pytest.mark.django_db
def test_form_view_field_options_conditions_manager_field_trashed(data_fixture):
    form_view = data_fixture.create_form_view()
    field = data_fixture.create_text_field(table=form_view.table)
    field_2 = data_fixture.create_text_field(table=form_view.table)
    options = data_fixture.create_form_view_field_option(form_view, field, enabled=True)
    data_fixture.create_form_view_field_options_condition(
        field_option=options, field=field_2
    )

    field_options = form_view.get_field_options()
    conditions = field_options[0].conditions.all()
    assert len(conditions) == 1

    field_2.trashed = True
    field_2.save()

    field_options = form_view.get_field_options()
    conditions = field_options[0].conditions.all()
    assert len(conditions) == 0


@pytest.mark.django_db
def test_public_view_password(data_fixture):
    form_view = data_fixture.create_form_view()
    # empty password means no password protection
    assert form_view.public_view_has_password is False
    assert form_view.check_public_view_password("whatever") is True
    # define a password and test it
    password = "12345678"
    form_view.set_password(password)
    assert form_view.public_view_has_password is True
    assert form_view.check_public_view_password("4321") is False
    assert form_view.check_public_view_password(password) is True
    # define a password using the static method
    password = "justanothercoolpassword"
    form_view.public_view_password = type(form_view).make_password(password)
    assert form_view.public_view_has_password is True
    assert form_view.check_public_view_password("4321") is False
    assert form_view.check_public_view_password(password) is True


@pytest.mark.django_db
def test_view_hierarchy(data_fixture):
    user = data_fixture.create_user()
    group = data_fixture.create_group(user=user)
    app = data_fixture.create_database_application(group=group, name="Test 1")
    table = data_fixture.create_database_table(name="Cars", database=app)
    grid_view = data_fixture.create_grid_view(table=table)
    assert grid_view.get_parent() == table
    assert grid_view.get_root() == group

    field = data_fixture.create_text_field(table=grid_view.table)
    grid_view_field_options = data_fixture.create_grid_view_field_option(
        grid_view, field
    )
    assert grid_view_field_options.get_parent() == grid_view
    assert grid_view_field_options.get_root() == group

    view_filter = data_fixture.create_view_filter(view=grid_view)
    assert view_filter.get_parent() == grid_view
    assert view_filter.get_root() == group

    view_sort = data_fixture.create_view_sort(view=grid_view)
    assert view_sort.get_parent() == grid_view
    assert view_sort.get_root() == group

    form_view = data_fixture.create_form_view(table=table)
    form_view_field_options = data_fixture.create_form_view_field_option(
        form_view, field
    )
    assert form_view_field_options.get_parent() == form_view
    assert form_view_field_options.get_root() == group
