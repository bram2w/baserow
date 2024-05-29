import { Registerable } from '@baserow/modules/core/registry'
import GeneralSidePanel from '@baserow/modules/builder/components/page/sidePanels/GeneralSidePanel'
import StyleSidePanel from '@baserow/modules/builder/components/page/sidePanels/StyleSidePanel'
import VisibilitySidePanel from '@baserow/modules/builder/components/page/sidePanels/VisibilitySidePanel'
import EventsSidePanel from '@baserow/modules/builder/components/page/sidePanels/EventsSidePanel'

export class pageSidePanelType extends Registerable {
  get label() {
    return null
  }

  get component() {
    return null
  }

  getDeactivatedText(element) {
    return ''
  }

  isDeactivated(element) {
    return false
  }

  getOrder() {
    return this.order
  }
}

export class GeneralPageSidePanelType extends pageSidePanelType {
  static getType() {
    return 'general'
  }

  get label() {
    return this.app.i18n.t('pageSidePanelType.general')
  }

  get component() {
    return GeneralSidePanel
  }

  getOrder() {
    return 10
  }
}

export class StylePageSidePanelType extends pageSidePanelType {
  static getType() {
    return 'style'
  }

  get label() {
    return this.app.i18n.t('pageSidePanelType.style')
  }

  get component() {
    return StyleSidePanel
  }

  getOrder() {
    return 20
  }
}

export class VisibilityPageSidePanelType extends pageSidePanelType {
  static getType() {
    return 'visibility'
  }

  get label() {
    return this.app.i18n.t('pageSidePanelType.visibility')
  }

  get component() {
    return VisibilitySidePanel
  }

  getOrder() {
    return 30
  }
}

export class EventsPageSidePanelType extends pageSidePanelType {
  static getType() {
    return 'events'
  }

  get label() {
    return this.app.i18n.t('pageSidePanelType.events')
  }

  get component() {
    return EventsSidePanel
  }

  getDeactivatedText(element) {
    const { i18n } = this.app
    return i18n.t('pageSidePanelType.eventsTabDeactivatedNoEvents')
  }

  isDeactivated(element) {
    const elementType = this.app.$registry.get('element', element.type)
    return elementType.getEvents(element).length === 0
  }

  getOrder() {
    return 40
  }
}
