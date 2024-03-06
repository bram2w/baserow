import { AppAuthProviderType } from '@baserow/modules/core/appAuthProviderTypes'
import LocalBaserowUserSourceForm from '@baserow_enterprise/integrations/localBaserow/components/appAuthProviders/LocalBaserowPasswordAppAuthProviderForm'
import { PasswordFieldType } from '@baserow/modules/database/fieldTypes'

export class LocalBaserowPasswordAppAuthProviderType extends AppAuthProviderType {
  static getType() {
    return 'local_baserow_password'
  }

  get name() {
    return this.app.i18n.t('appAuthProviderType.localBaserowPassword')
  }

  get formComponent() {
    return LocalBaserowUserSourceForm
  }

  /**
   * Returns the allowed field type list for the password field.
   * It's defined here so that it can be changed by a plugin.
   */
  get allowedPasswordFieldTypes() {
    return [PasswordFieldType.getType()]
  }

  getOrder() {
    return 10
  }
}
