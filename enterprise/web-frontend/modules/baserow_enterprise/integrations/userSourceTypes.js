import { UserSourceType } from '@baserow/modules/core/userSourceTypes'
import { LocalBaserowIntegrationType } from '@baserow/modules/integrations/integrationTypes'
import LocalBaserowUserSourceForm from '@baserow_enterprise/integrations/localBaserow/components/userSources/LocalBaserowUserSourceForm'
import localBaserowIntegration from '@baserow/modules/integrations/localBaserow/assets/images/localBaserowIntegration.svg'

export class LocalBaserowUserSourceType extends UserSourceType {
  static getType() {
    return 'local_baserow'
  }

  get integrationType() {
    return this.app.$registry.get(
      'integration',
      LocalBaserowIntegrationType.getType()
    )
  }

  get name() {
    return this.app.i18n.t('userSourceType.localBaserow')
  }

  get image() {
    return localBaserowIntegration
  }

  getSummary(userSource) {
    const integrations = this.app.store.getters['integration/getIntegrations']
    const integration = integrations.find(
      ({ id }) => id === userSource.integration_id
    )

    if (!integration) {
      return this.app.i18n.t('localBaserowUserSourceType.notConfigured')
    }

    if (!userSource.table_id) {
      return `${integration.name} - ${this.app.i18n.t(
        'localBaserowUserSourceType.notConfigured'
      )}`
    }

    for (const database of integration.context_data.databases) {
      for (const table of database.tables) {
        if (table.id === userSource.table_id) {
          const summaryParts = [integration.name, table.name]
          if (!userSource.email_field_id || !userSource.name_field_id) {
            summaryParts.push(
              this.app.i18n.t('localBaserowUserSourceType.notConfigured')
            )
          }
          return summaryParts.join(' - ')
        }
      }
    }

    return ''
  }

  get formComponent() {
    return LocalBaserowUserSourceForm
  }

  getOrder() {
    return 10
  }
}
