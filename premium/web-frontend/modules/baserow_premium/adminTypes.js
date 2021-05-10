import { AdminType } from '@baserow/modules/core/adminTypes'

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
    return 0
  }
}
