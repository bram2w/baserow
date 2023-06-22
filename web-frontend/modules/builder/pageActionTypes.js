import { Registerable } from '@baserow/modules/core/registry'

import PublishActionModal from '@baserow/modules/builder/components/page/header/PublishActionModal'

export class PageActionType extends Registerable {
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
    return 'div'
  }

  getOrder() {
    return 0
  }

  /**
   * By default, we will assume that the component is a context menu and will be
   * positioned next to the icon clicked on.
   */
  onClick({ component, button }) {
    component.toggle(button, 'bottom', 'left', 4)
  }
}

export class PublishPageActionType extends PageActionType {
  static getType() {
    return 'publish'
  }

  get label() {
    return this.app.i18n.t('pageActionTypes.publish')
  }

  get icon() {
    return 'upload'
  }

  get component() {
    return PublishActionModal
  }

  onClick({ component }) {
    component.show()
  }

  getOrder() {
    return 20
  }
}

export class PreviewPageActionType extends PageActionType {
  static getType() {
    return 'preview'
  }

  get label() {
    return this.app.i18n.t('pageActionTypes.preview')
  }

  onClick({ builder }) {
    const url = this.app.router.resolve({
      name: 'application-builder-page',
      params: { builderId: builder.id, pathMatch: '/' },
    }).href

    window.open(url, '_blank')
  }

  getOrder() {
    return 10
  }
}
