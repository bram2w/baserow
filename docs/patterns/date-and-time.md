# Dates and times

## Backend

### Time zones

- Use `datetime.timezone.utc` to represent UTC timezone
- Use `zoneinfo.ZoneInfo` object to represent any other timezone
- Use `datetime.tzinfo` as a type for a timezone
- Use `datetime.now` with tz set to UTC to get "now" datetime in UTC timezone
- Use `baserow.core.datetime.get_timezones` to get the list of all available timezones

```python
from zoneinfo import ZoneInfo
from datetime import datetime, timezone, tzinfo

# get a reference to UTC time zone
utc_timezone: tzinfo = timezone.utc

# get a reference to any other time zone
prague_timezone: tzinfo = ZoneInfo("Europe/Prague")

# create a new datetime in a timezone
my_datetime = datetime(..., tzinfo=timezone.utc)

# set a timezone to a datetime
my_datetime = my_datetime.replace(tzinfo=ZoneInfo("Europe/Prague"))

# convert a datetime into another timezone, preserving time in UTC
my_datetime = my_datetime.astimezone(tz=ZoneInfo("Europe/Prague"))

# get now in UTC
now = datetime.now(tz=timezone.utc)

# get all timezones
from baserow.core.datetime import get_timezones
all_timezones = get_timezones()
```

### References

- https://docs.python.org/3/library/datetime.html
- https://docs.python.org/3/library/zoneinfo.html
- https://docs.djangoproject.com/en/5.0/topics/i18n/timezones/