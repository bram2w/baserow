import { ViewDecoratorType } from '@baserow/modules/database/viewDecorators'
import PremiumModal from '@baserow_premium/components/PremiumModal'
import { PremiumPlugin } from '@baserow_premium/plugins'

import {
  GridViewType,
  GalleryViewType,
} from '@baserow/modules/database/viewTypes'

import { KanbanViewType } from './viewTypes'

import leftBorderDecoratorImage from '@baserow_premium/assets/images/leftBorderDecorator.svg'
import backgroundDecoratorImage from '@baserow_premium/assets/images/backgroundDecorator.svg'

import LeftBorderColorViewDecorator from '@baserow_premium/components/views/LeftBorderColorViewDecorator'
import BackgroundColorViewDecorator from '@baserow_premium/components/views/BackgroundColorViewDecorator'

export class LeftBorderColorViewDecoratorType extends ViewDecoratorType {
  static getType() {
    return 'left_border_color'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewDecoratorType.leftBorderColor')
  }

  getDescription() {
    const { i18n } = this.app
    return i18n.t('viewDecoratorType.leftBorderColorDescription')
  }

  getImage() {
    return leftBorderDecoratorImage
  }

  getPlace() {
    return 'first_cell'
  }

  getDeactivatedText() {
    const { i18n } = this.app
    return i18n.t('viewDecoratorType.onlyForPremium')
  }

  getDeactivatedClickModal() {
    return PremiumModal
  }

  isDeactivated(groupId) {
    const { store } = this.app

    const additionalUserData = store.getters['auth/getAdditionalUserData']

    if (PremiumPlugin.hasValidPremiumLicense(additionalUserData, groupId)) {
      return false
    }
    return true
  }

  canAdd({ view }) {
    const { i18n } = this.app

    if (view.decorations.some(({ type }) => type === this.getType())) {
      return [false, i18n.t('viewDecoratorType.onlyOneDecoratorPerView')]
    }
    return [true]
  }

  getComponent() {
    const { store } = this.app

    // Read from the store
    const additionalUserData = store.getters['auth/getAdditionalUserData']

    if (PremiumPlugin.hasValidPremiumLicense(additionalUserData)) {
      return LeftBorderColorViewDecorator
    }

    return null
  }

  isCompatible(view) {
    const { store } = this.app

    return (
      [
        GridViewType.getType(),
        GalleryViewType.getType(),
        KanbanViewType.getType(),
      ].includes(view.type) && !store.getters['page/view/public/getIsPublic']
    )
  }
}

export class BackgroundColorViewDecoratorType extends ViewDecoratorType {
  static getType() {
    return 'background_color'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewDecoratorType.backgroundColor')
  }

  getDescription() {
    const { i18n } = this.app
    return i18n.t('viewDecoratorType.backgroundColorDescription')
  }

  getImage() {
    return backgroundDecoratorImage
  }

  getPlace() {
    return 'wrapper'
  }

  getComponent() {
    const { store } = this.app

    // Read from the store
    const additionalUserData = store.getters['auth/getAdditionalUserData']

    if (PremiumPlugin.hasValidPremiumLicense(additionalUserData)) {
      return BackgroundColorViewDecorator
    }

    return null
  }

  isCompatible(view) {
    const { store } = this.app

    return (
      [
        GridViewType.getType(),
        GalleryViewType.getType(),
        KanbanViewType.getType(),
      ].includes(view.type) && !store.getters['page/view/public/getIsPublic']
    )
  }

  getDeactivatedText() {
    const { i18n } = this.app
    return i18n.t('viewDecoratorType.onlyForPremium')
  }

  getDeactivatedClickModal() {
    return PremiumModal
  }

  isDeactivated(groupId) {
    const { store } = this.app

    const additionalUserData = store.getters['auth/getAdditionalUserData']

    if (PremiumPlugin.hasValidPremiumLicense(additionalUserData, groupId)) {
      return false
    }
    return true
  }

  canAdd({ view }) {
    const { i18n } = this.app

    if (view.decorations.some(({ type }) => type === this.getType())) {
      return [false, i18n.t('viewDecoratorType.onlyOneDecoratorPerView')]
    }
    return [true]
  }
}
