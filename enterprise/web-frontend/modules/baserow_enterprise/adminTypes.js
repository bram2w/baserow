import { AdminType } from '@baserow/modules/core/adminTypes'
import EnterpriseFeatures from '@baserow_enterprise/features'

class EnterpriseAdminType extends AdminType {
  getDeactivatedText() {
    return this.app.i18n.t('enterprise.deactivated')
  }

  isDeactivated() {
    return !this.app.$hasFeature(EnterpriseFeatures.SSO)
  }
}

export class AuthProvidersType extends EnterpriseAdminType {
  static getType() {
    return 'auth-providers'
  }

  getIconClass() {
    return 'sign-in-alt'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('adminType.Authentication')
  }

  getRouteName() {
    return 'admin-auth-providers'
  }

  getOrder() {
    return 100
  }
}
