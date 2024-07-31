import { AdminType } from '@baserow/modules/core/adminTypes'
import PremiumFeatures from '@baserow_premium/features'
import PremiumModal from '@baserow_premium/components/PremiumModal'

class PremiumAdminType extends AdminType {
  isDeactivated() {
    return !this.app.$hasFeature(PremiumFeatures.PREMIUM)
  }

  getDeactivatedModal() {
    return PremiumModal
  }
}

export class DashboardType extends PremiumAdminType {
  static getType() {
    return 'dashboard'
  }

  getIconClass() {
    return 'iconoir-home-simple'
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

  getCategory() {
    const { i18n } = this.app
    return i18n.t('sidebar.people')
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
    return 'baserow-icon-groups'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('premium.adminType.workspaces')
  }

  getCategory() {
    const { i18n } = this.app
    return i18n.t('sidebar.people')
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

  getCategory() {
    const { i18n } = this.app
    return i18n.t('sidebar.licenses')
  }

  getRouteName() {
    return 'admin-licenses'
  }

  getOrder() {
    return 10000
  }
}
