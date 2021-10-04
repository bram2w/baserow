from django.db import models
from django.db.models.fields.related_descriptors import (
    ForwardManyToOneDescriptor,
    ManyToManyDescriptor,
)
from django.utils.functional import cached_property


class SingleSelectForwardManyToOneDescriptor(ForwardManyToOneDescriptor):
    def get_queryset(self, **hints):
        """
        We specifically want to return a new query set without the provided hints
        because the related table could be in another database and that could fail
        otherwise.
        """

        return self.field.remote_field.model.objects.all()

    def get_object(self, instance):
        """
        Tries to fetch the reference object, but if it fails because it doesn't exist,
        the value will be set to None instead of failing hard.
        """

        try:
            return super().get_object(instance)
        except self.field.remote_field.model.DoesNotExist:
            setattr(instance, self.field.name, None)
            instance.save()
            return None


class SingleSelectForeignKey(models.ForeignKey):
    forward_related_accessor_class = SingleSelectForwardManyToOneDescriptor


class MultipleSelectManyToManyDescriptor(ManyToManyDescriptor):
    """
    This is a slight modification of Djangos default ManyToManyDescriptor for the
    MultipleSelectFieldType. This is needed in order to change the default ordering of
    the select_options that are being returned when accessing those by calling ".all()"
    on the field. The default behavior was that no ordering is applied, which in the
    case for the MultipleSelectFieldType meant that the select options were ordered by
    their ID. To show the select_options in the order of how the user added those to
    the field, the "get_queryset" method was modified by applying an order_by. The
    order_by is using the id of the through table.
    """

    @cached_property
    def related_manager_cls(self):
        manager_class = super().related_manager_cls

        class CustomManager(manager_class):
            def _apply_rel_ordering(self, queryset):
                return queryset.extra(order_by=[f"{self.through._meta.db_table}.id"])

            def get_queryset(self):
                try:
                    return self.instance._prefetched_objects_cache[
                        self.prefetch_cache_name
                    ]
                except (AttributeError, KeyError):
                    queryset = super().get_queryset()
                    return self._apply_rel_ordering(queryset)

        return CustomManager


class MultipleSelectManyToManyField(models.ManyToManyField):
    """
    This is a slight modification of Djangos default ManyToManyField to be used with
    the MultipleSelectFieldType. A custom ManyToManyField is needed in order to apply
    the custom ManyToManyDescriptor (MultipleSelectManyToManyDescriptor) to the class
    of the model (on which the ManyToManyField gets added) as well as the related class.
    """

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        setattr(
            cls,
            self.name,
            MultipleSelectManyToManyDescriptor(self.remote_field, reverse=False),
        )

    def contribute_to_related_class(self, cls, related):
        super().contribute_to_related_class(cls, related)
        if (
            not self.remote_field.is_hidden()
            and not related.related_model._meta.swapped
        ):
            setattr(
                cls,
                related.get_accessor_name(),
                MultipleSelectManyToManyDescriptor(self.remote_field, reverse=True),
            )
