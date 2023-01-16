import os


def setup(settings):
    """
    This function is called after Baserow as setup its own Django settings file but
    before Django starts. Read and modify provided settings object as appropriate
    just like you would in a normal Django settings file. E.g.:

    settings.INSTALLED_APPS += ["some_custom_plugin_dep"]
    for db, value in settings.DATABASES:
        value['engine'] = 'some custom engine'
    """

    settings.BASEROW_ENTERPRISE_AUDIT_LOG_CLEANUP_INTERVAL_MINUTES = int(
        os.getenv("BASEROW_ENTERPRISE_AUDIT_LOG_CLEANUP_INTERVAL_MINUTES", 24 * 60)
    )

    settings.BASEROW_ENTERPRISE_AUDIT_LOG_RETENTION_DAYS = int(
        os.getenv("BASEROW_ENTERPRISE_AUDIT_LOG_RETENTION_DAYS", 365)
    )
