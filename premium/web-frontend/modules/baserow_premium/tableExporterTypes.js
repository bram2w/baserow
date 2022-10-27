import { TableExporterType } from '@baserow/modules/database/exporterTypes'
import { GridViewType } from '@baserow/modules/database/viewTypes'
import TableJSONExporter from '@baserow_premium/components/exporter/TableJSONExporter'
import TableXMLExporter from '@baserow_premium/components/exporter/TableXMLExporter'
import PremiumModal from '@baserow_premium/components/PremiumModal'
import PremiumFeatures from '@baserow_premium/features'

class PremiumTableExporterType extends TableExporterType {
  getDeactivatedText() {
    return this.app.i18n.t('premium.deactivated')
  }

  getDeactivatedClickModal() {
    return PremiumModal
  }

  isDeactivated(groupId) {
    return !this.app.$hasFeature(PremiumFeatures.PREMIUM, groupId)
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
    const { i18n } = this.app
    return i18n.t('premium.exporterType.json')
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
    const { i18n } = this.app
    return i18n.t('premium.exporterType.xml')
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
