import { AdminType } from '@baserow/modules/core/adminTypes'
import PremiumFeatures from '@baserow_premium/features'

class PremiumAdminType extends AdminType {
  getDeactivatedText() {
    return this.app.i18n.t('premium.deactivated')
  }

  isDeactivated() {
    return !this.app.$hasFeature(PremiumFeatures.PREMIUM)
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
    const { i18n } = this.app
    return i18n.t('premium.adminType.dashboard')
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
    const { i18n } = this.app
    return i18n.t('premium.adminType.users')
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
    const { i18n } = this.app
    return i18n.t('premium.adminType.groups')
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
    const { i18n } = this.app
    return i18n.t('premium.adminType.licenses')
  }

  getRouteName() {
    return 'admin-licenses'
  }

  getOrder() {
    return 10000
  }
}
