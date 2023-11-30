from typing import Dict, List, Optional

from baserow.core.registry import CustomFieldsInstanceMixin


class PublicCustomFieldsInstanceMixin(CustomFieldsInstanceMixin):
    public_serializer_field_names = []
    """The field names that must be added to the serializer if it's public."""

    public_request_serializer_field_names = []
    """
    The field names that must be added to the public request serializer if different
    from the `public_serializer_field_names`.
    """

    request_serializer_field_overrides = None
    """
    The fields that must be added to the request serializer if different from the
    `serializer_field_overrides` property.
    """

    public_serializer_field_overrides = None
    """The fields that must be added to the public serializer."""

    public_request_serializer_field_overrides = None
    """
    The fields that must be added to the public request serializer if different from the
    `public_serializer_field_overrides` property.
    """

    def get_field_overrides(
        self, request_serializer: bool, extra_params=None, **kwargs
    ) -> Dict:
        public = extra_params.get("public", False)

        if public:
            if (
                request_serializer
                and self.public_request_serializer_field_overrides is not None
            ):
                return self.public_request_serializer_field_overrides
            else:
                return self.public_serializer_field_overrides

        return super().get_field_overrides(request_serializer, extra_params, **kwargs)

    def get_field_names(
        self, request_serializer: bool, extra_params=None, **kwargs
    ) -> List[str]:
        public = extra_params.get("public", False)

        if public:
            if (
                request_serializer
                and self.public_request_serializer_field_names is not None
            ):
                return self.public_request_serializer_field_names
            else:
                return self.public_serializer_field_names

        return super().get_field_names(request_serializer, extra_params, **kwargs)

    def get_meta_ref_name(
        self,
        request_serializer: bool,
        extra_params=None,
        **kwargs,
    ) -> Optional[str]:
        meta_ref_name = super().get_meta_ref_name(
            request_serializer, extra_params, **kwargs
        )

        public = extra_params.get("public", False)

        if public:
            meta_ref_name = f"Public{meta_ref_name}"

        return meta_ref_name
