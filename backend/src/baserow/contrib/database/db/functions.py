from django.db.models import Func, UUIDField


class RandomUUID(Func):
    # We're using this function because the `gen_random_uuid` has introduced in
    # version 13, and we support a lower version than that.
    # More information about where we found this function:
    # https://stackoverflow.com/questions/12505158/generating-a-uuid-in-postgres-for-insert-statement
    template = "uuid_in(overlay(overlay(md5(random()::text || ':' || random()::text) placing '4' from 13) placing to_hex(floor(random()*(11-8+1) + 8)::int)::text from 17)::cstring)"
    output_field = UUIDField()
