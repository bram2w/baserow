from rest_framework import serializers

from baserow.contrib.database.views.models import GalleryViewFieldOptions


class GalleryViewFieldOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GalleryViewFieldOptions
        fields = ("hidden", "order")
