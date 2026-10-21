import { lazyComponent } from '@baserow/modules/core/utils/lazyComponent'
import { TwoWaySyncStrategyType } from '@baserow/modules/database/twoWaySyncStrategyTypes'
import { DataSyncPaidFeature } from '@baserow_enterprise/paidFeatures'
import EnterpriseFeatures from '@baserow_enterprise/features'

const PaidFeaturesModal = lazyComponent(
  () => import('@baserow_premium/components/PaidFeaturesModal.vue')
)

export class RealtimePushTwoWaySyncStrategyType extends TwoWaySyncStrategyType {
  static getType() {
    return 'realtime_push'
  }

  getDescription() {
    const { $i18n } = this.app
    return $i18n.t('enterpriseTwoWaySyncStrategyType.realtimePushDescription')
  }

  isDeactivated(workspaceId) {
    return !this.app.$hasFeature(EnterpriseFeatures.DATA_SYNC, workspaceId)
  }

  getDeactivatedClickModal() {
    return [
      PaidFeaturesModal,
      { 'initial-selected-type': DataSyncPaidFeature.getType() },
    ]
  }
}
