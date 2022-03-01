class CoreExportSerializedStructure:
    @staticmethod
    def application(id, name, order, type):
        return {
            "id": id,
            "name": name,
            "order": order,
            "type": type,
        }
