from collections import OrderedDict
from typing import List, Type

from baserow.contrib.database.api.export.serializers import (
    CsvExporterOptionsSerializer,
    BaseExporterOptionsSerializer,
)
from baserow.contrib.database.export.file_writer import (
    QuerysetSerializer,
    FileWriter,
)
from baserow.contrib.database.export.registries import (
    TableExporter,
)
from baserow.contrib.database.views.view_types import GridViewType


class CsvTableExporter(TableExporter):
    type = "csv"

    @property
    def option_serializer_class(self) -> Type[BaseExporterOptionsSerializer]:
        return CsvExporterOptionsSerializer

    @property
    def can_export_table(self) -> bool:
        return True

    @property
    def supported_views(self) -> List[str]:
        return [GridViewType.type]

    @property
    def file_extension(self) -> str:
        return ".csv"

    @property
    def queryset_serializer_class(self):
        return CsvQuerysetSerializer


class CsvQuerysetSerializer(QuerysetSerializer):
    def __init__(self, queryset, ordered_field_objects):
        super().__init__(queryset, ordered_field_objects)

        self.headers = OrderedDict({"id": "id"})

        for field_object in ordered_field_objects:
            field_database_name = field_object["name"]
            field_display_name = field_object["field"].name
            self.headers[field_database_name] = field_display_name

    def write_to_file(
        self,
        file_writer: FileWriter,
        export_charset="utf-8",
        csv_column_separator=",",
        csv_include_header=True,
    ):
        """
        Writes the queryset to the provided file in csv format using the provided
        options.

        :param file_writer: The file writer to use to do the writing.
        :param csv_column_separator: The character used to separate columns in the
            resulting csv file.
        :param csv_include_header: Whether or not to include a header in the resulting
            csv file.
        :param export_charset: The charset to write to the file using.
        """

        # add BOM to support utf-8 CSVs in MS Excel (for Windows only)
        if export_charset == "utf-8":
            file_writer.write_bytes(b"\xef\xbb\xbf")

        csv_dict_writer = file_writer.get_csv_dict_writer(
            self.headers.keys(), encoding=export_charset, delimiter=csv_column_separator
        )

        if csv_include_header:
            csv_dict_writer.writerow(self.headers)

        def write_row(row, _):
            data = {}
            for field_serializer in self.field_serializers:
                field_database_name, _, field_human_value = field_serializer(row)
                data[field_database_name] = self._value_to_csv(field_human_value)

            csv_dict_writer.writerow(data)

        file_writer.write_rows(self.queryset, write_row)

    def _value_to_csv(self, val):
        """
        Converts a python value to a csv suitable value. For lists it joins them with
        commas, for dicts it turns them into a space separated key=value single column
        value.

        :param val: A python value to convert to a suitable csv value.
        :return: A suitable csv value.
        """

        if isinstance(val, list):
            return ",".join([self._value_to_csv(inner_val) for inner_val in val])
        if isinstance(val, dict):
            return " ".join(
                [
                    f"{key}={self._value_to_csv(inner_val)}"
                    for key, inner_val in val.items()
                ]
            )
        return str(val)
