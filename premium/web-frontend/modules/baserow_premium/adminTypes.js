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
    return 1
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
    return 2
  }
}

export class GroupsAdminType extends AdminType {
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
