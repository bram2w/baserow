from baserow.api.exceptions import UnknownFieldProvided


class UnknownFieldRaisesExceptionSerializerMixin:
    """
    Mixin to a DRF serializer class to raise an exception if data with unknown fields
    is provided to the serializer.
    """

    def __init__(self, *args, **kwargs):
        self._baserow_internal_initial_data = None
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        self._baserow_internal_initial_data = data
        return super().to_internal_value(data)

    @property
    def safe_initial_data(self):
        """
        Returns the initial data provided by the user to this serializer. Works for
        both top level serializers and model serializers and also nested serializers.

        For the highest serializer in the DRF Class hierarchy initial_data will
        be populated with the raw initial data provided by the user and so this property
        uses that when available.

        However, for nested serializers initial_data is not populated by DRF. The only
        way we can get access to the raw data provided by the user (so we can check
        what keys they provided by DRF ignores them by default) is by overriding
        `to_internal_value` above and keeping track of the data parameter.
        """

        if hasattr(self, "initial_data"):
            return self.initial_data
        else:
            return self._baserow_internal_initial_data

    def validate(self, data):
        safe_initial_data = self.safe_initial_data
        if safe_initial_data is not None:
            unknown_field_names = set(safe_initial_data.keys()) - set(
                self.fields.keys()
            )
            if unknown_field_names:
                unknown_field_names_csv = ", ".join(unknown_field_names)
                raise UnknownFieldProvided(
                    detail=f"Your request body had the following unknown attributes:"
                    f" {unknown_field_names_csv}. Please check the api documentation "
                    f"and only "
                    f"provide valid fields.",
                )

        return data
