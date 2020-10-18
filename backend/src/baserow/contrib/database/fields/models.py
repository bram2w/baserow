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

DATE_FORMAT = {
    'EU': {
        'name': 'European (D/M/Y)',
        'format': '%d/%m/%Y'
    },
    'US': {
        'name': 'US (M/D/Y)',
        'format': '%m/%d/%Y'
    },
    'ISO': {
        'name': 'ISO (Y-M-D)',
        'format': '%Y-%m-%d'
    },
}
DATE_FORMAT_CHOICES = [(k, v['name']) for k, v in DATE_FORMAT.items()]

DATE_TIME_FORMAT = {
    '24': {
        'name': '24 hour',
        'format': '%H:%M'
    },
    '12': {
        'name': '12 hour',
        'format': '%I:%M %p'
    }
}
DATE_TIME_FORMAT_CHOICES = [(k, v['name']) for k, v in DATE_TIME_FORMAT.items()]


def get_default_field_content_type():
    return ContentType.objects.get_for_model(Field)


class Field(OrderableMixin, PolymorphicContentTypeMixin, models.Model):
    """
    Because each field type can have custom settings, for example precision for a number
    field, values for an option field or checkbox style for a boolean field we need a
    polymorphic content type to store these settings in another table.
    """

    table = models.ForeignKey('database.Table', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(help_text='Lowest first.')
    name = models.CharField(max_length=255)
    primary = models.BooleanField(
        default=False,
        help_text='Indicates if the field is a primary field. If `true` the field '
                  'cannot be deleted and the value should represent the whole row.'
    )
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
    text_default = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='If set, this value is going to be added every time a new row '
                  'created.'
    )


class LongTextField(Field):
    pass


class URLField(Field):
    pass


class NumberField(Field):
    number_type = models.CharField(
        max_length=32,
        choices=NUMBER_TYPE_CHOICES,
        default=NUMBER_TYPE_INTEGER
    )
    number_decimal_places = models.IntegerField(
        choices=NUMBER_DECIMAL_PLACES_CHOICES,
        default=1,
        help_text='The amount of digits allowed after the point.'
    )
    number_negative = models.BooleanField(
        default=False,
        help_text='Indicates if negative values are allowed.'
    )

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


class DateField(Field):
    date_format = models.CharField(
        choices=DATE_FORMAT_CHOICES,
        default=DATE_FORMAT_CHOICES[0][0],
        max_length=32,
        help_text='EU (20/02/2020), US (02/20/2020) or ISO (2020-02-20)'
    )
    date_include_time = models.BooleanField(
        default=False,
        help_text='Indicates if the field also includes a time.'
    )
    date_time_format = models.CharField(
        choices=DATE_TIME_FORMAT_CHOICES,
        default=DATE_TIME_FORMAT_CHOICES[0][0],
        max_length=32,
        help_text='24 (14:30) or 12 (02:30 PM)'
    )

    def get_python_format(self):
        """
        Returns the strftime format as a string based on the field's properties. This
        could for example be '%Y-%m-%d %H:%I'.

        :return: The strftime format based on the field's properties.
        :rtype: str
        """

        date_format = DATE_FORMAT[self.date_format]['format']
        time_format = DATE_TIME_FORMAT[self.date_time_format]['format']

        if self.date_include_time:
            return f'{date_format} {time_format}'
        else:
            return date_format


class LinkRowField(Field):
    link_row_table = models.ForeignKey(
        'database.Table',
        on_delete=models.CASCADE,
        help_text='The table that the field has a relation with.',
        blank=True
    )
    link_row_related_field = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        help_text='The relation field in the other table.',
        null=True,
        blank=True
    )
    link_row_relation_id = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        Every LinkRow needs to have a unique relation id that is shared with the
        related link row field in the other table.
        """

        if self.link_row_relation_id is None:
            last_id = LinkRowField.objects.all().aggregate(
                largest=models.Max('link_row_relation_id')
            )['largest'] or 0
            self.link_row_relation_id = last_id + 1

        super().save(*args, **kwargs)

    @property
    def through_table_name(self):
        """
        Generating a unique through table name based on the relation id.

        :return: The table name of the through model.
        :rtype: string
        """

        if not self.link_row_relation_id:
            raise ValueError('The link row field does not yet have a relation id.')

        return f'database_relation_{self.link_row_relation_id}'


class EmailField(Field):
    pass
