import { DecoratorValueProviderType } from '@baserow/modules/database/decoratorValueProviders'

import SingleSelectColorValueProviderForm from '@baserow_premium/components/views/SingleSelectColorValueProviderForm'
import ConditionalColorValueProviderForm from '@baserow_premium/components/views/ConditionalColorValueProviderForm'
import {
  BackgroundColorViewDecoratorType,
  LeftBorderColorViewDecoratorType,
} from '@baserow_premium/viewDecorators'
import { uuid } from '@baserow/modules/core/utils/string'
import { randomColor } from '@baserow/modules/core/utils/colors'
import { matchSearchFilters } from '@baserow/modules/database/utils/view'

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
      field_id: firstSelectField?.id || null,
    }
  }
}

export class ConditionalColorValueProviderType extends DecoratorValueProviderType {
  static getType() {
    return 'conditional_color'
  }

  static getDefaultFilterConf(registry, { fields }) {
    const field = fields[0]
    const filter = { field: field.id }

    const viewFilterTypes = registry.getAll('viewFilter')
    const compatibleType = Object.values(viewFilterTypes).find(
      (viewFilterType) => {
        return viewFilterType.fieldIsCompatible(field)
      }
    )

    filter.type = compatibleType.type
    const viewFilterType = registry.get('viewFilter', filter.type)
    filter.value = viewFilterType.getDefaultValue(field)
    filter.preload_values = {}
    filter.id = uuid()

    return filter
  }

  static getDefaultColorConf(
    registry,
    { fields },
    noFilter = false,
    excludeColors = undefined
  ) {
    return {
      color: randomColor(excludeColors),
      operator: 'AND',
      filters: noFilter
        ? []
        : [
            ConditionalColorValueProviderType.getDefaultFilterConf(registry, {
              fields,
            }),
          ],
      id: uuid(),
    }
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
    const { $registry } = this.app
    for (const { color, filters, operator } of options.colors) {
      if (
        row.id !== -1 &&
        row.id !== undefined &&
        matchSearchFilters($registry, operator, filters, fields, row)
      ) {
        return color
      }
    }
    return ''
  }

  getCompatibleDecoratorTypes() {
    return [LeftBorderColorViewDecoratorType, BackgroundColorViewDecoratorType]
  }

  getFormComponent() {
    return ConditionalColorValueProviderForm
  }

  getDefaultConfiguration({ fields }) {
    const { $registry } = this.app
    return {
      default: null,
      colors: [
        ConditionalColorValueProviderType.getDefaultColorConf($registry, {
          fields,
        }),
      ],
    }
  }
}
