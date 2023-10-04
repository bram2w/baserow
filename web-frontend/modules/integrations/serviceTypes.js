import { ServiceType } from '@baserow/modules/core/serviceTypes'
import { LocalBaserowIntegrationType } from '@baserow/modules/integrations/integrationTypes'
import LocalBaserowGetRowForm from '@baserow/modules/integrations/components/services/LocalBaserowGetRowForm'
import LocalBaserowListRowsForm from '@baserow/modules/integrations/components/services/LocalBaserowListRowsForm'
import GenerateSchema from 'generate-schema'

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

  getDataSchema(applicationContext, service) {
    const page = applicationContext.page
    const dataSourceContents =
      this.app.store.getters['dataSourceContent/getDataSourceContents'](page)

    return GenerateSchema.json(dataSourceContents[service.id])
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

  get isCollection() {
    return true
  }

  getDataSchema(applicationContext, service) {
    const page = applicationContext.page
    const dataSourceContents =
      this.app.store.getters['dataSourceContent/getDataSourceContents'](page)

    return GenerateSchema.json(dataSourceContents[service.id])
  }

  getOrder() {
    return 20
  }
}
