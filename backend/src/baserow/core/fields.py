from django.db import models
from django.db.models.fields.related_descriptors import ReverseOneToOneDescriptor
from django.db.transaction import atomic


class SyncedDateTimeField(models.DateTimeField):
    def __init__(self, sync_with=None, sync_with_add=None, *args, **kwargs):
        self.sync_with = sync_with
        self.sync_with_add = sync_with_add
        if sync_with or sync_with_add:
            kwargs["editable"] = False
            kwargs["blank"] = True
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        if add and self.sync_with_add:
            value = getattr(model_instance, self.sync_with_add)
            setattr(model_instance, self.attname, value)
            return value
        elif self.sync_with:
            value = getattr(model_instance, self.sync_with)
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super().pre_save(model_instance, add)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.sync_with or self.sync_with_add:
            kwargs.pop("editable", None)
            kwargs.pop("blank", None)
        return name, path, args, kwargs


class AutoTrueBooleanField(models.BooleanField):
    """
    A `BooleanField` which automatically sets itself to `True` before a save takes
    place. Used by `ROW_NEEDS_BACKGROUND_UPDATE_COLUMN_NAME` to mark a row as
    needing a background update after it's been created or updated.
    """

    def pre_save(self, model_instance, add):
        setattr(model_instance, self.attname, True)
        return super().pre_save(model_instance, add)


class AutoSingleRelatedObjectDescriptor(ReverseOneToOneDescriptor):
    """
    The descriptor that handles the object creation for an AutoOneToOneField.

    This class is inspired by:
    https://github.com/skorokithakis/django-annoying/blob/master/annoying/fields.py
    """

    @atomic
    def __get__(self, instance, instance_type=None):
        model = getattr(self.related, "related_model", self.related.model)

        try:
            return super(AutoSingleRelatedObjectDescriptor, self).__get__(
                instance, instance_type
            )
        except model.DoesNotExist:
            # Using get_or_create instead() of save() or create() as it better handles
            # race conditions
            obj, _ = model.objects.get_or_create(**{self.related.field.name: instance})

            # Update Django's cache, otherwise first 2 calls to obj.relobj
            # will return 2 different in-memory objects
            self.related.set_cached_value(instance, obj)
            self.related.field.set_cached_value(obj, instance)
            return obj


class AutoOneToOneField(models.OneToOneField):
    """
    OneToOneField creates related object on first call if it doesn't exist yet.
    Use it instead of original OneToOne field.

    example:

        class MyProfile(models.Model):
            user = AutoOneToOneField(User, primary_key=True)
            home_page = models.URLField(max_length=255, blank=True)
            icq = models.IntegerField(max_length=255, null=True)
    """

    def contribute_to_related_class(self, cls, related):
        setattr(
            cls, related.get_accessor_name(), AutoSingleRelatedObjectDescriptor(related)
        )
