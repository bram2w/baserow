import { PermissionManagerType } from '@baserow/modules/core/permissionManagerTypes'

export class RolePermissionManagerType extends PermissionManagerType {
  static getType() {
    return 'role'
  }

  hasPermission(permissions, operation, context) {
    if (permissions[operation] === undefined) {
      return false
    }

    return (
      (permissions[operation].default &&
        !permissions[operation].exceptions.includes(context.id)) ||
      (!permissions[operation].default &&
        permissions[operation].exceptions.includes(context.id))
    )
  }
}
