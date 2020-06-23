from rest_framework import serializers

from baserow.contrib.database.table.models import Table


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ('id', 'name', 'order',)
        extra_kwargs = {
            'id': {
                'read_only': True
            },
            'order': {
                'help_text': 'Lowest first.'
            }
        }


class TableCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ('name',)
