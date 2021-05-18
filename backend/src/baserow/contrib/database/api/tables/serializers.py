from rest_framework import serializers

from baserow.contrib.database.table.models import Table


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = (
            "id",
            "name",
            "order",
            "database_id",
        )
        extra_kwargs = {
            "id": {"read_only": True},
            "database_id": {"read_only": True},
            "order": {"help_text": "Lowest first."},
        }


class TableCreateSerializer(serializers.ModelSerializer):
    data = serializers.ListField(
        min_length=1,
        child=serializers.ListField(
            child=serializers.CharField(
                help_text="The value of the cell.", allow_blank=True
            ),
            help_text="The row containing all the values.",
        ),
        default=None,
        help_text="A list of rows that needs to be created as initial table data. If "
        "not provided some example data is going to be created.",
    )
    first_row_header = serializers.BooleanField(
        default=False,
        help_text="Indicates if the first provided row is the header. If true the "
        "field names are going to be the values of the first row. Otherwise "
        'they will be called "Column N"',
    )

    class Meta:
        model = Table
        fields = ("name", "data", "first_row_header")
        extra_kwargs = {
            "data": {"required": False},
            "first_row_header": {"required": False},
        }


class TableUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ("name",)


class OrderTablesSerializer(serializers.Serializer):
    table_ids = serializers.ListField(
        child=serializers.IntegerField(), help_text="Table ids in the desired order."
    )
