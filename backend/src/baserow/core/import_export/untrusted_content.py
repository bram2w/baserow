from baserow.core.deferred_callbacks import register_deferred_callback


class UntrustedContentTypeMixin:
    """Marks active content in the cache belonging to one application copy."""

    def export_serialized(self, *args, **kwargs):
        if (cache := kwargs.get("cache")) is not None:
            cache["has_untrusted_content"] = True
        return super().export_serialized(*args, **kwargs)

    def import_serialized(
        self,
        parent,
        serialized_values,
        id_mapping,
        files_zip=None,
        storage=None,
        cache=None,
        **kwargs,
    ):
        """Import active content and mark the current application's cache."""

        if cache is not None:
            cache["has_untrusted_content"] = True
        return super().import_serialized(
            parent,
            serialized_values,
            id_mapping,
            files_zip=files_zip,
            storage=storage,
            cache=cache,
            **kwargs,
        )


def defer_untrusted_content_update(application, cache, import_export_config):
    """Finalize an external application's restriction after detecting active content.

    The closure retains this application's cache even when other applications are
    imported before deferred callbacks run. Update the returned model instance too,
    so API responses and subsequent publication see the persisted restriction.
    """

    if (
        import_export_config.is_duplicate
        or import_export_config.is_publishing
        or import_export_config.is_template
    ):
        return

    def update_untrusted_content():
        untrusted_content = cache.get("has_untrusted_content", False)
        if application.untrusted_content != untrusted_content:
            application.untrusted_content = untrusted_content
            application.save(update_fields=["untrusted_content"])

    register_deferred_callback(update_untrusted_content)
