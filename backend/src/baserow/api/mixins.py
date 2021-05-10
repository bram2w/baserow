from baserow.api.exceptions import UnknownFieldProvided


class UnknownFieldRaisesExceptionSerializerMixin:
    """
    Mixin to a DRF serializer class to raise an exception if data with unknown fields
    is provided to the serializer.
    """

    def validate(self, data):
        if hasattr(self, "initial_data"):
            unknown_keys = set(self.initial_data.keys()) - set(self.fields.keys())
            if unknown_keys:
                raise UnknownFieldProvided(
                    f"Received unknown fields: {unknown_keys}. Please check "
                    "the api documentation and only provide "
                    "valid fields."
                )

        return data
