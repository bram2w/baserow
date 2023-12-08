import { ServiceType } from '@baserow/modules/core/serviceTypes'
import { LocalBaserowIntegrationType } from '@baserow/modules/integrations/integrationTypes'
import LocalBaserowGetRowForm from '@baserow/modules/integrations/localBaserow/components/services/LocalBaserowGetRowForm'
import LocalBaserowListRowsForm from '@baserow/modules/integrations/localBaserow/components/services/LocalBaserowListRowsForm'

export class LocalBaserowGetRowServiceType extends ServiceType {
  static getType() {
    return 'local_baserow_get_row'
  }

  get name() {
    return this.app.i18n.t('serviceType.localBaserowGetRow')
  }

  get integrationType() {
    return this.app.$registry.get(
      'integration',
      LocalBaserowIntegrationType.getType()
    )
  }

  isValid(service) {
    return (
      super.isValid(service) &&
      Boolean(service.table_id) &&
      Boolean(service.row_id)
    )
  }

  get formComponent() {
    return LocalBaserowGetRowForm
  }

  getDataSchema(service) {
    return service.schema
  }

  /**
   * A hook called prior to an update to modify the filters and
   * sortings if the `table_id` changes from one ID to another.
   * The same behavior happens in the backend, this reset is to
   * make the filter/sort components reset properly.
   */
  beforeUpdate(newValues, oldValues) {
    if (
      oldValues.table_id !== null &&
      newValues.table_id !== oldValues.table_id
    ) {
      newValues.filters = []
      newValues.sortings = []
    }
    return newValues
  }

  getOrder() {
    return 10
  }
}

export class LocalBaserowListRowsServiceType extends ServiceType {
  static getType() {
    return 'local_baserow_list_rows'
  }

  get name() {
    return this.app.i18n.t('serviceType.localBaserowListRows')
  }

  get integrationType() {
    return this.app.$registry.get(
      'integration',
      LocalBaserowIntegrationType.getType()
    )
  }

  get formComponent() {
    return LocalBaserowListRowsForm
  }

  isValid(service) {
    return super.isValid(service) && Boolean(service.table_id)
  }

  get returnsList() {
    return true
  }

  getDataSchema(service) {
    return service.schema
  }

  get maxResultLimit() {
    return 100
  }

  getOrder() {
    return 20
  }
}
