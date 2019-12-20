from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.functional import cached_property


class OrderableMixin:
    """
    This mixin introduces a set of helpers of the model is orderable by a field.
    """

    @classmethod
    def get_highest_order_of_queryset(cls, queryset, field='order'):
        """

        :param queryset:
        :param field:
        :return:
        """

        return queryset.aggregate(
            models.Max(field)
        ).get(f'{field}__max', 0) or 0


class PolymorphicContentTypeMixin:
    """
    This mixin introduces a set of helpers for a model that has a polymorphic
    relationship with django's content type. Note that a foreignkey to the ContentType
    model must exist.

    Example:
        content_type = models.ForeignKey(
            ContentType,
            verbose_name='content type',
            related_name='applications',
            on_delete=models.SET(get_default_application_content_type)
        )
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not hasattr(self.__class__, 'content_type'):
            raise AttributeError(f'The attribute content_type doesn\'t exist on '
                                 f'{self.__class__.__name__}, but is required for the '
                                 f'PolymorphicContentTypeMixin.')

        if not self.id:
            if not self.content_type_id:
                self.content_type = ContentType.objects.get_for_model(self)

    @cached_property
    def specific(self):
        """Return this page in its most specific subclassed form."""

        content_type = ContentType.objects.get_for_id(self.content_type_id)
        model_class = self.specific_class
        if model_class is None:
            return self
        elif isinstance(self, model_class):
            return self
        else:
            return content_type.get_object_for_this_type(id=self.id)

    @cached_property
    def specific_class(self):
        """
        Return the class that this application would be if instantiated in its
        most specific form
        """

        content_type = ContentType.objects.get_for_id(self.content_type_id)
        return content_type.model_class()
