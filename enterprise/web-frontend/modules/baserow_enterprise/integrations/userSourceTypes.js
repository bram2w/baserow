import { UserSourceType } from '@baserow/modules/core/userSourceTypes'
import { LocalBaserowIntegrationType } from '@baserow/modules/integrations/integrationTypes'
import LocalBaserowUserSourceForm from '@baserow_enterprise/integrations/localBaserow/components/userSources/LocalBaserowUserSourceForm'
import localBaserowIntegration from '@baserow/modules/integrations/localBaserow/assets/images/localBaserowIntegration.svg'

import {
  TextFieldType,
  LongTextFieldType,
  EmailFieldType,
  NumberFieldType,
  UUIDFieldType,
} from '@baserow/modules/database/fieldTypes'

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

  /**
   * Returns the allowed field type list for the email field.
   * It's defined here so that it can be changed by a plugin.
   */
  get allowedEmailFieldTypes() {
    return [
      TextFieldType.getType(),
      LongTextFieldType.getType(),
      EmailFieldType.getType(),
    ]
  }

  /**
   * Returns the allowed field type list for the name field.
   * It's defined here so that it can be changed by a plugin.
   */
  get allowedNameFieldTypes() {
    return [
      TextFieldType.getType(),
      LongTextFieldType.getType(),
      EmailFieldType.getType(),
      NumberFieldType.getType(),
      UUIDFieldType.getType(),
    ]
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

  getLoginOptions(userSource) {
    if (!userSource.email_field_id || !userSource.name_field_id) {
      return {}
    }
    if (userSource.auth_providers.length !== 1) {
      return {}
    }
    const authProvider = userSource.auth_providers[0]
    if (
      authProvider.type !== 'local_baserow_password' ||
      !authProvider.password_field_id
    ) {
      return {}
    }
    return { password: {} }
  }

  getOrder() {
    return 10
  }
}
