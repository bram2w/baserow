import { Registerable } from '@baserow/modules/core/registry'
import PageSettings from '@baserow/modules/builder/components/page/settings/PageSettings'

export class PageSettingType extends Registerable {
  static getType() {
    return null
  }

  get name() {
    return null
  }

  get icon() {
    return null
  }

  get component() {
    return null
  }
}

export class PagePageSettingsType extends PageSettingType {
  static getType() {
    return 'page'
  }

  get name() {
    return this.app.i18n.t('pageSettingsTypes.pageName')
  }

  get icon() {
    return 'cogs'
  }

  get component() {
    return PageSettings
  }
}
