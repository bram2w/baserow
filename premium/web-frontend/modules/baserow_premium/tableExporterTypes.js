import { TableExporterType } from '@baserow/modules/database/exporterTypes'
import { GridViewType } from '@baserow/modules/database/viewTypes'
import TableJSONExporter from '@baserow_premium/components/exporter/TableJSONExporter'
import TableXMLExporter from '@baserow_premium/components/exporter/TableXMLExporter'

export class JSONTableExporter extends TableExporterType {
  getType() {
    return 'json'
  }

  getIconClass() {
    return 'file-code'
  }

  getName() {
    return 'Export to JSON'
  }

  getFormComponent() {
    return TableJSONExporter
  }

  getCanExportTable() {
    return true
  }

  getSupportedViews() {
    return [new GridViewType().getType()]
  }
}

export class XMLTableExporter extends TableExporterType {
  getType() {
    return 'xml'
  }

  getIconClass() {
    return 'file-code'
  }

  getName() {
    return 'Export to XML'
  }

  getFormComponent() {
    return TableXMLExporter
  }

  getCanExportTable() {
    return true
  }

  getSupportedViews() {
    return [new GridViewType().getType()]
  }
}
