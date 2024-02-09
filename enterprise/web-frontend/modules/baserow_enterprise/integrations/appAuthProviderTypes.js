import { AppAuthProviderType } from '@baserow/modules/core/appAuthProviderTypes'
import LocalBaserowUserSourceForm from '@baserow_enterprise/integrations/localBaserow/components/appAuthProviders/LocalBaserowPasswordAppAuthProviderForm'

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

  getOrder() {
    return 10
  }
}
