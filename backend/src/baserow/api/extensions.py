from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.plumbing import force_instance


class PolymorphicMappingSerializerExtension(OpenApiSerializerExtension):
    """
    This OpenAPI serializer extension makes it possible to easily define polymorphic
    relationships. It can be used for a response and request.

    Example:
        @auto_schema(
            responses={
                200: PolymorphicMappingSerializer(
                    'ExampleName',
                    {
                        'car': CarSerializer,
                        'boat': BoarSerializer
                    },
                    many=True
                ),
            }
        )
    """

    target_class = "baserow.api.utils.PolymorphicMappingSerializer"

    def get_name(self):
        return self.target.component_name

    def map_serializer(self, auto_schema, direction):
        return self._map_serializer(auto_schema, direction, self.target.mapping)

    def _map_serializer(self, auto_schema, direction, mapping):
        sub_components = []

        for key, serializer_class in mapping.items():
            sub_serializer = force_instance(serializer_class)
            resolved_sub_serializer = auto_schema.resolve_serializer(
                sub_serializer, direction
            )
            sub_components.append((key, resolved_sub_serializer.ref))

        return {
            "oneOf": [ref for _, ref in sub_components],
            "discriminator": {
                "propertyName": self.target.type_field_name,
                "mapping": {
                    resource_type: ref["$ref"] for resource_type, ref in sub_components
                },
            },
        }


class PolymorphicCustomFieldRegistrySerializerExtension(
    PolymorphicMappingSerializerExtension
):
    """
    This OpenAPI serializer extension automatically generates a mapping of the
    `CustomFieldsInstanceMixin` in the `CustomFieldsRegistryMixin`. The type will be
    the key and the serializer will be the value.

    Example:
        @auto_schema(
            responses={
                200: PolymorphicCustomFieldRegistrySerializer(
                    'ExampleName',
                    field_type_registry,
                    many=True
                ),
            }
        )
    """

    target_class = "baserow.api.utils.PolymorphicCustomFieldRegistrySerializer"

    def get_name(self):
        part_1 = self.target.registry.name.title()
        part_2 = self.target.base_class.__name__
        return f"{part_1}{part_2}"

    def map_serializer(self, auto_schema, direction):
        mapping = {
            types.type: types.get_serializer_class(base_class=self.target.base_class)
            for types in self.target.registry.registry.values()
        }

        return self._map_serializer(auto_schema, direction, mapping)
