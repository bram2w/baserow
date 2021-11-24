import { AdminType } from '@baserow/modules/core/adminTypes'
import { PremiumPlugin } from '@baserow_premium/plugins'

class PremiumAdminType extends AdminType {
  getDeactivatedText() {
    return this.app.i18n.t('premium.deactivated')
  }

  isDeactivated() {
    return !PremiumPlugin.hasValidPremiumLicense(
      this.app.store.getters['auth/getAdditionalUserData']
    )
  }
}

export class DashboardType extends PremiumAdminType {
  static getType() {
    return 'dashboard'
  }

  getIconClass() {
    return 'chart-line'
  }

  getName() {
    return 'Dashboard'
  }

  getRouteName() {
    return 'admin-dashboard'
  }

  getOrder() {
    return 1
  }
}

export class UsersAdminType extends PremiumAdminType {
  static getType() {
    return 'users'
  }

  getIconClass() {
    return 'users'
  }

  getName() {
    return 'Users'
  }

  getRouteName() {
    return 'admin-users'
  }

  getOrder() {
    return 2
  }
}

export class GroupsAdminType extends PremiumAdminType {
  static getType() {
    return 'groups'
  }

  getIconClass() {
    return 'layer-group'
  }

  getName() {
    return 'Groups'
  }

  getRouteName() {
    return 'admin-groups'
  }

  getOrder() {
    return 3
  }
}

export class LicensesAdminType extends AdminType {
  static getType() {
    return 'licenses'
  }

  getIconClass() {
    return 'certificate'
  }

  getName() {
    return 'Licenses'
  }

  getRouteName() {
    return 'admin-licenses'
  }

  getOrder() {
    return 10000
  }
}
