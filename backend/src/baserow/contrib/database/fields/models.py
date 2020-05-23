from django.db import models
from django.contrib.contenttypes.models import ContentType

from baserow.core.utils import to_snake_case, remove_special_characters
from baserow.core.mixins import OrderableMixin, PolymorphicContentTypeMixin


NUMBER_TYPE_INTEGER = 'INTEGER'
NUMBER_TYPE_DECIMAL = 'DECIMAL'
NUMBER_TYPE_CHOICES = (
    ('INTEGER', 'Integer'),
    ('DECIMAL', 'Decimal'),
)

NUMBER_DECIMAL_PLACES_CHOICES = (
    (1, '1.0'),
    (2, '1.00'),
    (3, '1.000'),
    (4, '1.0000'),
    (5, '1.00000')
)


def get_default_field_content_type():
    return ContentType.objects.get_for_model(Field)


class Field(OrderableMixin, PolymorphicContentTypeMixin, models.Model):
    """
    Because each field type can have custom settings, for example precision for a number
    field, values for an option field or checkbox style for a boolean field we need a
    polymorphic content type to store these settings in another table.
    """

    table = models.ForeignKey('database.Table', on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    name = models.CharField(max_length=255)
    primary = models.BooleanField(default=False)
    content_type = models.ForeignKey(
        ContentType,
        verbose_name='content type',
        related_name='database_fields',
        on_delete=models.SET(get_default_field_content_type)
    )

    class Meta:
        ordering = ('-primary', 'order',)

    @classmethod
    def get_last_order(cls, table):
        queryset = Field.objects.filter(table=table)
        return cls.get_highest_order_of_queryset(queryset) + 1

    @property
    def db_column(self):
        return f'field_{self.id}'

    @property
    def model_attribute_name(self):
        """
        Generates a pascal case based model attribute name based on the field name.

        :return: The generated model attribute name.
        :rtype: str
        """

        name = remove_special_characters(self.name, False)
        name = to_snake_case(name)

        if name[0].isnumeric():
            name = f'field_{name}'

        return name


class TextField(Field):
    text_default = models.CharField(max_length=255, null=True, blank=True)


class LongTextField(Field):
    pass


class NumberField(Field):
    number_type = models.CharField(max_length=32, choices=NUMBER_TYPE_CHOICES,
                                   default=NUMBER_TYPE_INTEGER)
    number_decimal_places = models.IntegerField(choices=NUMBER_DECIMAL_PLACES_CHOICES,
                                                default=1)
    number_negative = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """Check if the number_type and number_decimal_places has a valid choice."""
        if not any(self.number_type in _tuple for _tuple in NUMBER_TYPE_CHOICES):
            raise ValueError(f'{self.number_type} is not a valid choice.')
        if not any(
            self.number_decimal_places in _tuple
            for _tuple in NUMBER_DECIMAL_PLACES_CHOICES
        ):
            raise ValueError(f'{self.number_decimal_places} is not a valid choice.')
        super(NumberField, self).save(*args, **kwargs)


class BooleanField(Field):
    pass
