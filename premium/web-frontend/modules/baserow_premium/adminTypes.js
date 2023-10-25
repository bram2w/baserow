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
    return 'iconoir-candlestick-chart'
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
    return 'iconoir-community'
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

export class WorkspacesAdminType extends PremiumAdminType {
  static getType() {
    return 'workspaces'
  }

  getIconClass() {
    return 'iconoir-book-stack'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('premium.adminType.workspaces')
  }

  getRouteName() {
    return 'admin-workspaces'
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
    return 'iconoir-shield-check'
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
