from django.contrib.contenttypes.models import ContentType
from django.db import models

import pytest

from baserow.contrib.database.fields.models import get_default_field_content_type
from baserow.core.mixins import PolymorphicContentTypeMixin


@pytest.mark.django_db
def test_get_all_parents_and_self_with_single_model(data_fixture):
    class TmpModel(PolymorphicContentTypeMixin, models.Model):
        name = models.CharField()
        content_type = models.ForeignKey(
            ContentType,
            verbose_name="content type",
            related_name="database_fields",
            on_delete=models.SET(get_default_field_content_type),
        )

        class Meta:
            app_label = "test"

    model = TmpModel(name="a")
    assert model.all_parents_and_self() == [model]


@pytest.mark.django_db
def test_get_all_parents_and_self_with_one_level_of_inheritance(data_fixture):
    class RootParent(PolymorphicContentTypeMixin, models.Model):
        name = models.CharField()
        content_type = models.ForeignKey(
            ContentType,
            verbose_name="content type",
            related_name="database_fields",
            on_delete=models.CASCADE,
        )

        class Meta:
            app_label = "test"

    class SubModel(RootParent):
        class Meta:
            app_label = "test"

    parent_model = RootParent(name="a")
    model = SubModel(name="a", rootparent_ptr=parent_model)
    assert model.all_parents_and_self() == [parent_model, model]
    assert parent_model.all_parents_and_self() == [parent_model]


@pytest.mark.django_db
def test_get_all_parents_and_self_with_two_levels_of_inheritance(data_fixture):
    class RootParent2(PolymorphicContentTypeMixin, models.Model):
        name = models.CharField()
        content_type = models.ForeignKey(
            ContentType,
            verbose_name="content type",
            related_name="database_fields",
            on_delete=models.CASCADE,
        )

        class Meta:
            app_label = "test"

    class SubModel2(RootParent2):
        class Meta:
            app_label = "test"

    class SubSubModel(SubModel2):
        class Meta:
            app_label = "test"

    parent_model = RootParent2(name="a")
    sub_model = SubModel2(name="a", rootparent2_ptr=parent_model)
    sub_sub_model = SubSubModel(name="a", submodel2_ptr=sub_model)
    assert sub_sub_model.all_parents_and_self() == [
        parent_model,
        sub_model,
        sub_sub_model,
    ]
    assert sub_model.all_parents_and_self() == [
        parent_model,
        sub_model,
    ]
    assert parent_model.all_parents_and_self() == [
        parent_model,
    ]


@pytest.mark.django_db
def test_cant_define_model_with_multiple_parents_with_poly_mixin(data_fixture):
    class ParentA(PolymorphicContentTypeMixin, models.Model):
        name = models.CharField()
        content_type = models.ForeignKey(
            ContentType,
            verbose_name="content type",
            related_name="database_fields",
            on_delete=models.CASCADE,
        )

        class Meta:
            app_label = "test"

    class ParentB(PolymorphicContentTypeMixin, models.Model):
        other = models.CharField()
        content_type = models.ForeignKey(
            ContentType,
            verbose_name="content type",
            related_name="database_fields",
            on_delete=models.CASCADE,
        )

        class Meta:
            app_label = "test"

    class SubModel3(ParentA, ParentB):
        class Meta:
            app_label = "test"

    with pytest.raises(AttributeError, match="does not support multiple inheritance"):
        SubModel3(name="a")
