from django.conf import settings


class TablesDatabaseRouter(object):
    """
    This database router is used to check if the model is a generated table model. If so
    the configurable USER_TABLE_DATABASE connection must be used instead of the default
    one. This is so that the user tables can be stored into another database.
    """

    @staticmethod
    def user_table_database_if_generated_table_database(model):
        return (
            settings.USER_TABLE_DATABASE
            if hasattr(model, '_generated_table_model') else
            None
        )

    def db_for_read(self, model, **hints):
        return self.user_table_database_if_generated_table_database(model)

    def db_for_write(self, model, **hints):
        return self.user_table_database_if_generated_table_database(model)
