import json
from collections import OrderedDict
from typing import Type, List

from baserow.contrib.database.api.export.serializers import (
    BaseExporterOptionsSerializer,
)
from baserow.contrib.database.export.file_writer import (
    QuerysetSerializer,
    FileWriter,
)
from baserow.contrib.database.export.registries import TableExporter
from baserow.contrib.database.views.view_types import GridViewType

from .utils import get_unique_name, safe_xml_tag_name, to_xml


class JSONQuerysetSerializer(QuerysetSerializer):
    def write_to_file(self, file_writer: FileWriter, export_charset="utf-8"):
        """
        Writes the queryset to the provided file in json format. Will generate
        semi-structured json based on the fields in the queryset.
        The root element is a json list and will look like:
        [
            {...},
            {...}
        ]
        Where each row in the queryset is a dict of key-values in the returned json
        array.

        :param file_writer: The file writer to use to do the writing.
        :param export_charset: The charset to write to the file using.
        """

        file_writer.write("[\n", encoding=export_charset)

        def write_row(row, last_row):
            data = {}
            for field_serializer in self.field_serializers:
                _, field_name, field_csv_value = field_serializer(row)
                field_name = get_unique_name(data, field_name, separator=" ")
                data[field_name] = field_csv_value

            file_writer.write(json.dumps(data, indent=4), encoding=export_charset)
            if not last_row:
                file_writer.write(",\n", encoding=export_charset)

        file_writer.write_rows(self.queryset, write_row)
        file_writer.write("\n]\n", encoding=export_charset)


class JSONTableExporter(TableExporter):
    type = "json"

    @property
    def queryset_serializer_class(self) -> Type["QuerysetSerializer"]:
        return JSONQuerysetSerializer

    @property
    def option_serializer_class(self) -> Type[BaseExporterOptionsSerializer]:
        return BaseExporterOptionsSerializer

    @property
    def can_export_table(self) -> bool:
        return True

    @property
    def supported_views(self) -> List[str]:
        return [GridViewType.type]

    @property
    def file_extension(self) -> str:
        return ".json"


class XMLQuerysetSerializer(QuerysetSerializer):
    def write_to_file(self, file_writer: FileWriter, export_charset="utf-8"):
        """
        Writes the queryset to the provided file in xml format. Will generate
        semi-structured xml based on the fields in the queryset. Each separate row in
        the queryset will have an xml element like so:
        <rows>
            <row>...</row>
            <row>...</row>
        </rows>

        :param file_writer: The file writer to use to do the writing.
        :param export_charset: The charset to write to the file using.
        """

        file_writer.write(
            f'<?xml version="1.0" encoding="{export_charset}" ?>\n<rows>\n',
            encoding=export_charset,
        )

        def write_row(row, _):
            data = OrderedDict()
            for field_serializer in self.field_serializers:
                _, field_name, field_xml_value = field_serializer(row)
                field_name = safe_xml_tag_name(
                    field_name, "field-", _.replace("_", "-")
                )
                field_name = get_unique_name(data, field_name, separator="-")
                data[field_name] = field_xml_value

            row_xml = to_xml(
                {"row": data},
            )
            file_writer.write(row_xml + "\n", encoding=export_charset)

        file_writer.write_rows(self.queryset, write_row)
        file_writer.write("</rows>\n", encoding=export_charset)


class XMLTableExporter(TableExporter):
    type = "xml"

    @property
    def queryset_serializer_class(self) -> Type["QuerysetSerializer"]:
        return XMLQuerysetSerializer

    @property
    def option_serializer_class(self) -> Type[BaseExporterOptionsSerializer]:
        return BaseExporterOptionsSerializer

    @property
    def can_export_table(self) -> bool:
        return True

    @property
    def supported_views(self) -> List[str]:
        return [GridViewType.type]

    @property
    def file_extension(self) -> str:
        return ".xml"
