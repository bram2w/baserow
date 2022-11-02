import { Registerable } from '@baserow/modules/core/registry'

/**
 */
export class PermissionManagerType extends Registerable {
  hasPermission(permissions, operation, context) {}

  /**
   * The order value used to sort admin types in the sidebar menu.
   */
  getOrder() {
    return 0
  }

  /**
   * Translation mappings for all the roles that have been added by your
   * permission manager
   */
  getRolesTranslations() {
    return {}
  }
}

export class CorePermissionManagerType extends PermissionManagerType {
  static getType() {
    return 'core'
  }

  hasPermission(permissions, operation, context) {
    if (permissions.includes(operation)) {
      return true
    }
  }
}

export class StaffPermissionManagerType extends PermissionManagerType {
  static getType() {
    return 'staff'
  }

  hasPermission(permissions, operation, context) {
    if (permissions.staff_only_operations.includes(operation)) {
      return permissions.is_staff
    }
  }
}

export class GroupMemberPermissionManagerType extends PermissionManagerType {
  static getType() {
    return 'member'
  }

  hasPermission(permissions, operation, context) {
    return permissions
  }
}

export class BasicPermissionManagerType extends PermissionManagerType {
  static getType() {
    return 'basic'
  }

  getRolesTranslations() {
    const { i18n } = this.app

    return {
      ADMIN: {
        name: i18n.t('permission.admin'),
        description: i18n.t('permission.adminDescription'),
      },
      MEMBER: {
        name: i18n.t('permission.member'),
        description: i18n.t('permission.memberDescription'),
      },
    }
  }

  hasPermission(permissions, operation, context) {
    // Is it an admin only operation?
    if (permissions.admin_only_operations.includes(operation)) {
      // yes, so it should be an admin of the group
      if (permissions.is_admin) {
        // It is!
        return true
      }
    } else {
      // It's a member and it's a non admin only operation.
      return true
    }
    // None of the above applied
    return false
  }
}
