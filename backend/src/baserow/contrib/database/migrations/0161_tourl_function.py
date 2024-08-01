from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("database", "0160_merge_20240715_1319"),
    ]

    operations = [
        migrations.RunSQL(
            (
                r"""
CREATE OR REPLACE FUNCTION try_cast_to_url(input_text TEXT)
RETURNS TEXT AS $$
BEGIN
    IF input_text ~ '^(?:([a-zA-Z]+):\/\/)?(?:([a-zA-Z0-9._%+-]+)(:[a-zA-Z0-9._%+-]+)?@)?([a-zA-Z0-9.-]+)(?::(\d+))?(\/[^?]*)?(\?.*)?(#.*)?$' THEN
        RETURN input_text;
    ELSE
        RETURN '';
    END IF;
END;
$$ LANGUAGE plpgsql;
"""
            ),
            "DROP FUNCTION IF EXISTS try_cast_to_url(text);",
        ),
    ]
