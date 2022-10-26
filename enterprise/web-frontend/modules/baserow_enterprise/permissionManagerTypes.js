import { PermissionManagerType } from '@baserow/modules/core/permissionManagerTypes'

export class RolePermissionManagerType extends PermissionManagerType {
  static getType() {
    return 'role'
  }

  getRolesTranslations() {
    return {
      ADMIN: {
        name: 'roles.admin.name',
        description: 'roles.admin.description',
      },
      BUILDER: {
        name: 'roles.builder.name',
        description: 'roles.builder.description',
      },
      EDITOR: {
        name: 'roles.editor.name',
        description: 'roles.editor.description',
      },
      COMMENTER: {
        name: 'roles.commenter.name',
        description: 'roles.commenter.description',
      },
      VIEWER: {
        name: 'roles.viewer.name',
        description: 'roles.viewer.description',
      },
    }
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
