import { Registerable } from '@baserow/modules/core/registry'

/**
 * An admin type is visible in the sidebar under the admin menu item. All
 * registered admin types are visible in the sidebar to admins and he clicks
 * on one he is redirected to the route related to the admin type.
 */
export class AdminType extends Registerable {
  /**
   * The font awesome 5 icon name that is used as convenience for the user to
   * recognize admin types. The icon will for example be displayed in the
   * sidebar. If you for example want the database icon, you must return
   * 'database' here. This will result in the classname 'fas fa-database'.
   */
  getIconClass() {
    return null
  }

  /**
   * A human readable name of the admin type. This will be shown in the sidebar
   * if the user is an admin.
   */
  getName() {
    return null
  }

  /**
   * The order value used to sort admin types in the sidebar menu.
   */
  getOrder() {
    return 1
  }

  getRouteName() {
    throw new Error('The route name of an admin type must be set.')
  }

  constructor() {
    super()
    this.type = this.getType()
    this.iconClass = this.getIconClass()
    this.name = this.getName()
    this.routeName = this.getRouteName()

    if (this.type === null) {
      throw new Error('The type name of an admin type must be set.')
    }
    if (this.iconClass === null) {
      throw new Error('The icon class of an admin type must be set.')
    }
    if (this.name === null) {
      throw new Error('The name of an admin type must be set.')
    }
  }

  /**
   * @return object
   */
  serialize() {
    return {
      type: this.type,
      iconClass: this.iconClass,
      name: this.name,
      routeName: this.routeName,
    }
  }
}

export class SettingsAdminType extends AdminType {
  static getType() {
    return 'settings'
  }

  getIconClass() {
    return 'cogs'
  }

  getName() {
    return 'Settings'
  }

  getRouteName() {
    return 'admin-settings'
  }
}
