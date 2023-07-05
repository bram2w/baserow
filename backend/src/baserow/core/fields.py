from django.db import models


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
