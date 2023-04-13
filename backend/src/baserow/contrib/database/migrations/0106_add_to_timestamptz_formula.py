from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("database", "0105_formulafield_needs_periodic_update"),
    ]

    operations = [
        migrations.RunSQL(
            (
                """
create or replace function try_cast_to_date_tz(
    p_in text,
    p_format text,
    p_timezone text
)
    returns timestamptz
as
$$
declare
        original_timezone text;
        tstamp timestamptz := null;
begin
    original_timezone := current_setting('TIMEZONE');
    begin
        PERFORM set_config('timezone', p_timezone, true /* local */) ;
        tstamp := to_timestamp(p_in, p_format);
    exception when others then
        null;
    end;
   PERFORM set_config('timezone', original_timezone, true /* local */);
   return tstamp;
end;
$$
    language plpgsql;
"""
            ),
            ("DROP FUNCTION IF EXISTS try_cast_to_date_tz(text, text, text);"),
        )
    ]
