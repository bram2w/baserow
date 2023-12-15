from collections import OrderedDict
from typing import Any

from rest_framework import serializers
from rest_framework.fields import empty


class PolymorphicSerializer(serializers.Serializer):
    """
    This class is meant to be use with polymorphic models. It create the related
    polymorphic DRF serializer.
    """

    # The base serializer used to generate the serializer for the model.
    base_class: Any

    # The name of the type property to use to get the type
    type_field_name: str = "type"

    # The polymorphic registry for the model
    registry: Any

    def get_type_from_type_name(self, name):
        return self.registry.get(name)

    def get_type_from_instance(self, instance):
        return self.registry.get_by_model(instance)

    def get_type_from_mapping(self, mapping):
        return self.registry.get(mapping[self.type_field_name])

    def to_representation(self, instance):
        if not self.required and not instance:
            return None
        if isinstance(instance, OrderedDict):
            instance_type = self.get_type_from_mapping(instance)
        else:
            instance = instance.specific
            instance_type = self.get_type_from_instance(instance)

        serializer = instance_type.get_serializer(
            instance_type.model_class, base_class=self.base_class
        )
        ret = serializer.to_representation(instance)
        ret[self.type_field_name] = instance_type.type
        return ret

    def to_internal_value(self, data):
        if self.partial and self.instance:
            instance_type = self.get_type_from_instance(self.instance)
        else:
            instance_type = self.get_type_from_mapping(data)

        serializer = instance_type.get_serializer(
            instance_type.model_class, base_class=self.base_class
        )
        ret = serializer.to_internal_value(data)
        return ret

    def create(self, validated_data):
        type_name = validated_data.pop(self.type_field_name)
        instance_type = self.get_type_from_type_name(type_name)
        serializer = instance_type.get_serializer(
            instance_type.model_class, base_class=self.base_class
        )

        return serializer.create(validated_data)

    def update(self, instance, validated_data):
        type_name = validated_data.pop(self.type_field_name)
        instance_type = self.get_type_from_type_name(type_name)
        serializer = instance_type.get_serializer(
            instance_type.model_class, base_class=self.base_class
        )

        return serializer.update(instance, validated_data)

    def is_valid(self, *args, **kwargs):
        valid = super().is_valid(*args, **kwargs)

        try:
            if self.partial and self.instance:
                instance_type = self.get_type_from_instance(self.instance)
            else:
                instance_type = self.get_type_from_mapping(self.initial_data)

            serializer = instance_type.get_serializer(
                instance_type.model_class, base_class=self.base_class
            )
        except serializers.ValidationError:
            child_valid = False
        else:
            child_valid = serializer.is_valid(*args, **kwargs)
            self._errors.update(serializer.errors)
        return valid and child_valid

    def run_validation(self, data=empty):
        if not self.required and data == empty:
            return {}
        if self.partial and self.instance:
            instance_type = self.get_type_from_instance(self.instance)
        elif "type" in data:
            instance_type = self.get_type_from_mapping(data)
        else:
            self.fail("Unable to determine the `type` of the polymorphic data.")

        serializer = instance_type.get_serializer(
            instance_type.model_class, base_class=self.base_class
        )

        validated_data = serializer.run_validation(data)
        validated_data[self.type_field_name] = instance_type.type
        return validated_data
