sql_drop_try_cast = "DROP FUNCTION IF EXISTS pg_temp.try_cast(text, int)"
sql_create_try_cast = """
    create or replace function pg_temp.try_cast(
        p_in text,
        p_default int default null
    )
        returns %(type)s
    as
    $FUNCTION$
    begin
        begin
            %(alter_column_prepare_old_value)s
            %(alter_column_prepare_new_value)s
            return p_in::%(type)s;
        exception when others then
            return p_default;
        end;
    end;
    $FUNCTION$
    language plpgsql;
"""
