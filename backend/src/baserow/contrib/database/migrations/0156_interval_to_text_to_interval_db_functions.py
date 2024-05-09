from django.db import migrations

sql_script = r"""
create or replace function br_interval_to_text(in_val interval, in_format text, ms_prec int) returns text as
$$
    /**
      Converts interval value to text according to a given format.
      The difference from a regular to_char(interval, text) call is:
      * input value is normalized to positive number of seconds
      * if there's a day marker in format string, normalized interval value
        is adjusted so hours value is below 24 (with justify_hours)
      * if input value was negative one, the minus sign will be added to the value at the end.
      * a negative input value doesn't give interval-compatible value in result. It should be
        parsed to interval using br_text_to_interval(text, text) function.
      * if a milisecond marker is provided (`MS`) a rounding may be applied. If a third parameter is provided,
        it will be used to round and truncate miliseconds value to a given precision.
        The precision value should be in range 0..3. If precision is not provided, and
        milisecond


    Examples:

      br_interval_to_text(interval '-1d -23:22:21.0234', 'FMDD"d" HH24"h" MI"m"') -> '-1d 23h 22m'

      br_interval_to_text(interval '-1d -23:22:21.0234', 'FMDD"d" HH24"h" MI"m" SS.MS', 2) -> '-1d 23h 22m 21.02'

      br_interval_to_text(interval '-1d -23:22:21.0264', 'FMDD"d" HH24"h" MI"m" SS.MS', 2) -> '-1d 23h 22m 21.03'

      br_interval_to_text(interval '-1d -23:22:21.0234', 'HH24"h" MI"m"') -> '-47h 22m'

     */
    declare
        _formatted text;
        _interval interval;
        _total_secs double precision;
    begin
    _total_secs = abs(round(extract(epoch from br_interval_to_text.in_val)::numeric, coalesce(ms_prec, 3)));

    _interval = make_interval(secs=>_total_secs);

    /* if we have days in required format, we want to adjust hours to be in 00..24 range
           so 30h becomes 1d 6h
       otherwise, 30h remains 30h
           */
    if in_format ~ 'DD' then
        _interval = justify_hours(_interval);
    end if;

    _formatted =         case when br_interval_to_text.in_val < make_interval(secs=> 0) then '-' else '' end ||
        to_char( _interval, br_interval_to_text.in_format);

    /* this trick here removes trailing digits if MS is used in format and there's a precision set */
    if (in_format ~ '.MS$' and ms_prec is not null and (ms_prec -3 < 0)) then
        _formatted = left(    _formatted, (ms_prec-3));
    end if;

    return _formatted;

    end;
$$
    language plpgsql;

create or replace function _br_parse_from_text(in_val text, in_re text) returns double precision as
    $$
    /**
      Parse input text value to a double precision if regexp provided allows for that.
      If not, NULL is returned.

      _br_parse_from_text('1d 22.01', '\d+d (\d+.\d+)') -> 22.01
      _br_parse_from_text('1d 22.01', NULL) -> NULL

     */
    declare
        _re_result text;
    begin
    select into _re_result coalesce((regexp_match(in_val, coalesce(in_re, '')))[1], '');
    if _re_result <> '' then
        return _re_result::double precision;
    else
        return NULL;
    end if;
    end;
    $$ language plpgsql;

create or replace function br_text_to_interval(in_val text, in_day_re text, in_hour_re text, in_minute_re text, in_sec_re text) returns interval as
$$
    /**
      Parses text value describing interval value (created with br_interval_to_text function
      into an interval value.

      in_day_re, in_hour_re, in_minute_re and in_sec_re should be regular expressions
      that parse a specific part of the interval from in_val. Each regexp will be executed
      on in_val, so it can also note previous parts. If all regexps will not match and
      internally return NULL values, this function will return NULL value as well.

      Note that internally all calculations are processed on seconds, so raw results
      won't have year to day part of the interval, even if the number of hours exceeded
      24h. You should use justify_hours() to normalize the result.

      br_text_to_interval('-1d 23h:22m', r'^(\d+)d', r'^\d+d\s*(\d+)h', r'^\d+d\s*\d+h:(\d+)m', null) -> '-47:22:00'
      br_text_to_interval('-1d 23h:22m', r'^(\d+):\d+\d+', NULL, NULL, null) -> NULL

      br_text_to_interval('-1d 10:20:30.47', r'^(\d+)d', r'^\d+d\s*(\d+):', r'^\d+d\s*\d+:(\d+):', r'^\d+d\s*\d+:\d+:(\d+\.?\d+)$') -> '-34:20:30.47'

     */
    declare
        _out_secs double precision := 0;
        _parsed double precision;
        _multi int :=1;
        _parsed_any bool :=false;
    begin

        if starts_with(trim(in_val), '-') then
            _multi = -1;
            in_val = ltrim(trim(in_val), '-');
        end if;

        select into _parsed _br_parse_from_text(in_val, in_day_re) * 24 * 3600;
        _out_secs = _out_secs + coalesce(_parsed, 0.0);
        _parsed_any = _parsed_any or _parsed is not null;

        select into _parsed _br_parse_from_text(in_val, in_hour_re) * 3600;
        _out_secs = _out_secs + coalesce(_parsed, 0.0);
        _parsed_any = _parsed_any or _parsed is not null;

        select into _parsed _br_parse_from_text(in_val, in_minute_re) * 60;
        _out_secs = _out_secs + coalesce(_parsed, 0.0);
        _parsed_any = _parsed_any or _parsed is not null;

        select into _parsed _br_parse_from_text(in_val, in_sec_re);
        _out_secs = _out_secs + coalesce(_parsed, 0.0);
        _parsed_any = _parsed_any or _parsed is not null;

        if _parsed_any then
            return make_interval(secs=>_out_secs * _multi);
        else
            return null;
        end if;
    end;
$$
    language plpgsql;
"""

reverse_sql_script = r"""
drop function if exists br_text_to_interval(text, text, text, text, text);
drop function if exists br_interval_to_text(interval, text);
drop function if exists _br_parse_from_text(text, text);
"""


class Migration(migrations.Migration):
    dependencies = [
        ("database", "0155_alter_durationfield_duration_format_and_more"),
    ]

    operations = [migrations.RunSQL(sql_script, reverse_sql=reverse_sql_script)]
