from django import forms
from django.core.validators import URLValidator
from django.db import models
from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor
from django.utils.translation import gettext_lazy as _


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


class URLTextField(models.TextField):
    """
    This is a slightly modified django.db.models.URLField. The difference is that this
    field is based on the TextField and does not have a max length.
    """

    default_validators = [URLValidator()]
    description = _("URL")

    def __init__(self, verbose_name=None, name=None, **kwargs):
        super().__init__(verbose_name, name, **kwargs)

    def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": forms.URLField,
                **kwargs,
            }
        )
