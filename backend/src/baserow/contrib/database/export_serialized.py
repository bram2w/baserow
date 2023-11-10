class DatabaseExportSerializedStructure:
    @staticmethod
    def database(tables):
        return {"tables": tables}

    @staticmethod
    def table(id, name, order, fields, views, rows):
        return {
            "id": id,
            "name": name,
            "order": order,
            "fields": fields,
            "views": views,
            "rows": rows,
        }

    @staticmethod
    def row(id, order, created_on, updated_on, last_modified_by=None):
        optional = {}

        if last_modified_by:
            optional["last_modified_by"] = last_modified_by.email

        return {
            "id": id,
            "order": order,
            "created_on": created_on,
            "updated_on": updated_on,
            **optional,
        }

    @staticmethod
    def file_field_value(name, visible_name, original_name):
        return {
            "name": name,
            "visible_name": visible_name,
            "original_name": original_name,
        }
