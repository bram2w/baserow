import { Registerable } from '@baserow/modules/core/registry'
import PasswordSettings from '@baserow/modules/core/components/settings/PasswordSettings'

/**
 * All settings types will be added to the settings modal.
 */
export class SettingsType extends Registerable {
  /**
   * The font awesome 5 icon name that is used as convenience for the user to
   * recognize setting types. The icon will for example be displayed in the modal
   * setting sidebar. If you for example want the database icon, you must return
   * 'database' here. This will result in the classname 'fas fa-database'.
   */
  getIconClass() {
    return null
  }

  /**
   * A human readable name of the settings type. This will be shown in the modal
   * settings sidebar.
   */
  getName() {
    return null
  }

  /**
   * The component will be rendered when the user clicks on the item in the settings
   * model.
   */
  getComponent() {
    throw new Error('The component of a settings type must be set.')
  }

  constructor(...args) {
    super(...args)
    this.type = this.getType()
    this.iconClass = this.getIconClass()

    if (this.type === null) {
      throw new Error('The type name of a settings type must be set.')
    }
    if (this.iconClass === null) {
      throw new Error('The icon class of a settings type must be set.')
    }
    if (this.name === null) {
      throw new Error('The name of a settings type must be set.')
    }
  }

  /**
   * @return object
   */
  serialize() {
    return {
      type: this.type,
      iconClass: this.iconClass,
      name: this.getName(),
    }
  }
}

export class PasswordSettingsType extends SettingsType {
  static getType() {
    return 'password'
  }

  getIconClass() {
    return 'lock'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('settingType.password')
  }

  getComponent() {
    return PasswordSettings
  }
}
