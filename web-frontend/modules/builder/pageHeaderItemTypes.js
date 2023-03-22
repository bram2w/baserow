import { Registerable } from '@baserow/modules/core/registry'
import ElementsContext from '@baserow/modules/builder/components/page/ElementsContext'
import DataSourceContext from '@baserow/modules/builder/components/page/DataSourceContext'
import VariablesContext from '@baserow/modules/builder/components/page/VariablesContext'
import SettingsModal from '@baserow/modules/builder/components/page/SettingsModal'

export class PageHeaderItemType extends Registerable {
  get label() {
    return null
  }

  get icon() {
    return null
  }

  /**
   * This is the component that will be opened when the icon is clicked. Usually this
   * is either a context or a modal.
   */
  get component() {
    return null
  }

  /**
   * By default, we will assume that the component is a context menu and will be
   * positioned next to the icon clicked on.
   */
  onClick(component, button) {
    component.toggle(button, 'bottom', 'left', 4)
  }
}

export class ElementsPageHeaderItemType extends PageHeaderItemType {
  getType() {
    return 'elements'
  }

  get label() {
    return this.app.i18n.t('pageHeaderItemTypes.labelElements')
  }

  get icon() {
    return 'stream'
  }

  get component() {
    return ElementsContext
  }
}

export class DataSourcesPageHeaderItemType extends PageHeaderItemType {
  getType() {
    return 'data_sources'
  }

  get label() {
    return this.app.i18n.t('pageHeaderItemTypes.labelDataSource')
  }

  get icon() {
    return 'table'
  }

  get component() {
    return DataSourceContext
  }
}

export class VariablesPageHeaderItemType extends PageHeaderItemType {
  getType() {
    return 'variables'
  }

  get label() {
    return this.app.i18n.t('pageHeaderItemTypes.labelVariables')
  }

  get icon() {
    return 'square-root-alt'
  }

  get component() {
    return VariablesContext
  }
}

export class SettingsPageHeaderItemType extends PageHeaderItemType {
  getType() {
    return 'settings'
  }

  get label() {
    return this.app.i18n.t('pageHeaderItemTypes.labelSettings')
  }

  get icon() {
    return 'square-root-alt'
  }

  get component() {
    return SettingsModal
  }

  onClick(component, button) {
    component.show()
  }
}
