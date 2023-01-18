def setup(settings):
    """
    This function is called after Baserow as setup its own Django settings file but
    before Django starts. Read and modify provided settings object as appropriate
    just like you would in a normal Django settings file. E.g.:

    settings.INSTALLED_APPS += ["some_custom_plugin_dep"]
    for db, value in settings.DATABASES:
        value['engine'] = 'some custom engine'
    """
