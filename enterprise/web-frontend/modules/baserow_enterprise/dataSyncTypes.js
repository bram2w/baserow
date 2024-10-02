import { DataSyncType } from '@baserow/modules/database/dataSyncTypes'

import LocalBaserowTableDataSync from '@baserow_enterprise/components/dataSync/LocalBaserowTableDataSync'
import EnterpriseFeatures from '@baserow_enterprise/features'
import EnterpriseModal from '@baserow_enterprise/components/EnterpriseModal'

export class LocalBaserowTableDataSyncType extends DataSyncType {
  static getType() {
    return 'local_baserow_table'
  }

  getIconClass() {
    return 'iconoir-menu'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('enterpriseDataSyncType.localBaserowTable')
  }

  getFormComponent() {
    return LocalBaserowTableDataSync
  }

  isDeactivated(workspaceId) {
    return !this.app.$hasFeature(EnterpriseFeatures.DATA_SYNC, workspaceId)
  }

  getDeactivatedClickModal() {
    return EnterpriseModal
  }
}
