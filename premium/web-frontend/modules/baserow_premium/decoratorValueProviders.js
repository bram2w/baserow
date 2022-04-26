import { DecoratorValueProviderType } from '@baserow/modules/database/decoratorValueProviders'

import SingleSelectColorValueProviderForm from '@baserow_premium/components/views/SingleSelectColorValueProviderForm'
import ConditionalColorValueProviderForm from '@baserow_premium/components/views/ConditionalColorValueProviderForm'
import {
  BackgroundColorViewDecoratorType,
  LeftBorderColorViewDecoratorType,
} from '@baserow_premium/viewDecorators'

export class SingleSelectColorValueProviderType extends DecoratorValueProviderType {
  static getType() {
    return 'single_select_color'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('decoratorValueProviderType.singleSelectColor')
  }

  getDescription() {
    const { i18n } = this.app
    return i18n.t('decoratorValueProviderType.singleSelectColorDescription')
  }

  getIconClass() {
    return 'chevron-circle-down'
  }

  getFormComponent() {
    return SingleSelectColorValueProviderForm
  }

  getCompatibleDecoratorTypes() {
    return [LeftBorderColorViewDecoratorType, BackgroundColorViewDecoratorType]
  }

  getValue({ options, fields, row }) {
    const value = row[`field_${options.field_id}`]
    return value?.color || ''
  }

  getDefaultConfiguration({ fields }) {
    const firstSelectField = fields.find(({ type }) => type === 'single_select')
    return {
      field_id: firstSelectField?.id,
    }
  }
}

export class ConditionalColorValueProviderType extends DecoratorValueProviderType {
  static getType() {
    return 'conditional_color'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('decoratorValueProviderType.conditionalColor')
  }

  getDescription() {
    const { i18n } = this.app
    return i18n.t('decoratorValueProviderType.conditionalColorDescription')
  }

  getIconClass() {
    return 'filter'
  }

  getValue({ options, fields, row }) {
    return ''
  }

  getCompatibleDecoratorTypes() {
    return [LeftBorderColorViewDecoratorType, BackgroundColorViewDecoratorType]
  }

  getFormComponent() {
    return ConditionalColorValueProviderForm
  }
}
