import { lazyComponent } from '@baserow/modules/core/utils/lazyComponent'
import { ConfigureDataSyncType } from '@baserow/modules/database/configureDataSyncTypes'

const ConfigureDataSyncPeriodicInterval = lazyComponent(
  () =>
    import('@baserow_enterprise/components/dataSync/ConfigureDataSyncPeriodicInterval')
)

export class PeriodicIntervalFieldsConfigureDataSyncType extends ConfigureDataSyncType {
  static getType() {
    return 'periodic-interval'
  }

  get name() {
    return this.app.$i18n.t('configureDataSyncModal.periodicInterval')
  }

  get iconClass() {
    return 'iconoir-timer'
  }

  get component() {
    return ConfigureDataSyncPeriodicInterval
  }
}
