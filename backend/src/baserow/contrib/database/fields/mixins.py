from django.db import models
import pytz


DATE_FORMAT = {
    "EU": {"name": "European (D/M/Y)", "format": "%d/%m/%Y", "sql": "DD/MM/YYYY"},
    "US": {"name": "US (M/D/Y)", "format": "%m/%d/%Y", "sql": "MM/DD/YYYY"},
    "ISO": {"name": "ISO (Y-M-D)", "format": "%Y-%m-%d", "sql": "YYYY-MM-DD"},
}
DATE_FORMAT_CHOICES = [(k, v["name"]) for k, v in DATE_FORMAT.items()]

DATE_TIME_FORMAT = {
    "24": {"name": "24 hour", "format": "%H:%M", "sql": "HH24:MI"},
    "12": {"name": "12 hour", "format": "%I:%M %p", "sql": "HH12:MIAM"},
}
DATE_TIME_FORMAT_CHOICES = [(k, v["name"]) for k, v in DATE_TIME_FORMAT.items()]


def get_date_time_format(options, format_type):
    date_format_for_type = DATE_FORMAT[options.date_format][format_type]
    time_format_for_type = DATE_TIME_FORMAT[options.date_time_format][format_type]
    if options.date_include_time:
        return f"{date_format_for_type} {time_format_for_type}"
    else:
        return date_format_for_type


class BaseDateMixin(models.Model):
    date_format = models.CharField(
        choices=DATE_FORMAT_CHOICES,
        default=DATE_FORMAT_CHOICES[0][0],
        max_length=32,
        help_text="EU (20/02/2020), US (02/20/2020) or ISO (2020-02-20)",
    )
    date_include_time = models.BooleanField(
        default=False, help_text="Indicates if the field also includes a time."
    )
    date_time_format = models.CharField(
        choices=DATE_TIME_FORMAT_CHOICES,
        default=DATE_TIME_FORMAT_CHOICES[0][0],
        max_length=32,
        help_text="24 (14:30) or 12 (02:30 PM)",
    )

    class Meta:
        abstract = True

    def get_python_format(self):
        """
        Returns the strftime format as a string based on the field's properties. This
        could for example be '%Y-%m-%d %H:%I'.

        :return: The strftime format based on the field's properties.
        :rtype: str
        """

        return self._get_format("format")

    def get_psql_format(self):
        """
        Returns the sql datetime format as a string based on the field's properties.
        This could for example be 'YYYY-MM-DD HH12:MIAM'.

        :return: The sql datetime format based on the field's properties.
        :rtype: str
        """

        return self._get_format("sql")

    def get_psql_type(self):
        """
        Returns the postgresql column type used by this field depending on if it is a
        date or datetime.

        :return: The postgresql column type either 'timestamp' or 'date'
        :rtype: str
        """

        return "timestamp" if self.date_include_time else "date"

    def get_psql_type_convert_function(self):
        """
        Returns the postgresql function that can be used to coerce another postgresql
        type to the correct type used by this field.

        :return: The postgresql type conversion function, either 'TO_TIMESTAMP' or
        'TO_DATE'
        :rtype: str
        """

        return "TO_TIMESTAMP" if self.date_include_time else "TO_DATE"

    def _get_format(self, format_type):
        return get_date_time_format(self, format_type)


class TimezoneMixin(models.Model):
    timezone = models.CharField(
        max_length=255,
        blank=False,
        help_text="Timezone of User during field creation.",
        default="UTC",
    )

    def get_timezone(self, fallback="UTC"):
        return self.timezone if self.timezone in pytz.all_timezones else fallback

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """Check if the timezone is a valid choice."""

        if self.timezone not in pytz.all_timezones:
            raise ValueError(f"{self.timezone} is not a valid choice.")
        super().save(*args, **kwargs)
