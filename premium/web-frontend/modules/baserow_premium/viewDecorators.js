import { ViewDecoratorType } from '@baserow/modules/database/viewDecorators'
import PremiumModal from '@baserow_premium/components/PremiumModal'

import {
  GridViewType,
  GalleryViewType,
} from '@baserow/modules/database/viewTypes'

import { KanbanViewType } from './viewTypes'

import leftBorderDecoratorImage from '@baserow_premium/assets/images/leftBorderDecorator.svg'
import backgroundDecoratorImage from '@baserow_premium/assets/images/backgroundDecorator.svg'

import LeftBorderColorViewDecorator from '@baserow_premium/components/views/LeftBorderColorViewDecorator'
import BackgroundColorViewDecorator from '@baserow_premium/components/views/BackgroundColorViewDecorator'
import PremiumFeatures from '@baserow_premium/features'

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
    return !this.app.$hasFeature(PremiumFeatures.PREMIUM, groupId)
  }

  canAdd({ view }) {
    const { i18n } = this.app

    if (view.decorations.some(({ type }) => type === this.getType())) {
      return [false, i18n.t('viewDecoratorType.onlyOneDecoratorPerView')]
    }
    return [true]
  }

  getComponent(groupId) {
    if (!this.isDeactivated(groupId)) {
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

  getComponent(groupId) {
    if (!this.isDeactivated(groupId)) {
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
    return !this.app.$hasFeature(PremiumFeatures.PREMIUM, groupId)
  }

  canAdd({ view }) {
    const { i18n } = this.app

    if (view.decorations.some(({ type }) => type === this.getType())) {
      return [false, i18n.t('viewDecoratorType.onlyOneDecoratorPerView')]
    }
    return [true]
  }
}
