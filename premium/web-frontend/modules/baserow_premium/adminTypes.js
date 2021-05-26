import { AdminType } from '@baserow/modules/core/adminTypes'

export class DashboardType extends AdminType {
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
    return 0
  }
}

export class UsersAdminType extends AdminType {
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
    return 1
  }
}
