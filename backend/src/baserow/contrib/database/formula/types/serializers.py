from rest_framework import serializers
from rest_framework.fields import CharField


class LinkSerializer(serializers.Serializer):
    url = CharField()
    label = CharField(allow_null=True, allow_blank=True)
