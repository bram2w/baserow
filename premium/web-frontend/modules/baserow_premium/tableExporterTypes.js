import { TableExporterType } from '@baserow/modules/database/exporterTypes'
import { GridViewType } from '@baserow/modules/database/viewTypes'
import { PremiumPlugin } from '@baserow_premium/plugins'
import TableJSONExporter from '@baserow_premium/components/exporter/TableJSONExporter'
import TableXMLExporter from '@baserow_premium/components/exporter/TableXMLExporter'

class PremiumTableExporterType extends TableExporterType {
  getDeactivatedText() {
    return this.app.i18n.t('premium.deactivated')
  }

  isDeactivated() {
    return !PremiumPlugin.hasValidPremiumLicense(
      this.app.store.getters['auth/getAdditionalUserData']
    )
  }
}

export class JSONTableExporter extends PremiumTableExporterType {
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
    return [GridViewType.getType()]
  }
}

export class XMLTableExporter extends PremiumTableExporterType {
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
    return [GridViewType.getType()]
  }
}
