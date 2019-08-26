from rest_framework import serializers

from baserow.core.models import Group, GroupUser


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name',)
        extra_kwargs = {
            'id': {
                'read_only': True
            }
        }


class GroupUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupUser
        fields = ('order',)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(GroupSerializer(instance.group).data)
        return data


class OrderGroupsSerializer(serializers.Serializer):
    groups = serializers.ListField(child=serializers.IntegerField())
