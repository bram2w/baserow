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

  getOrder() {
    return 40
  }
}
