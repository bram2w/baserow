import { Registerable } from '@baserow/modules/core/registry'
import GenericViewAggregation from '@baserow/modules/database/components/aggregation/GenericViewAggregation'

export class ViewAggregationType extends Registerable {
  /**
   * A human readable name of the aggregation type.
   */
  getName() {
    return null
  }

  /**
   * A human readable name of the aggregation type to display in the menu.
   */
  getShortName() {
    return this.getName()
  }

  /**
   * Returns the raw aggregation type which is used by the backend to compute the
   * aggregation.
   */
  getRawType() {
    return this.getType()
  }

  /**
   * Should return the field type names that the aggregation is compatible with or
   * functions which take a field and return a boolean indicating if the field is
   * compatible or not.
   *
   * So for example ['text', 'long_text']. You can create this type of aggregation
   * only for `text` and `long_text` field type.
   *
   * Or using a function you could do [(field) => field.some_prop === 10, 'long_text']
   * and then fields which pass the test defined by the function will be deemed as
   * compatible.
   *
   */
  getCompatibleFieldTypes() {
    return []
  }

  /**
   * Returns if a given field is compatible with this view aggregation or not.
   * Uses the list provided by getCompatibleFieldTypes to calculate this.
   */
  fieldIsCompatible(field) {
    for (const typeOrFunc of this.getCompatibleFieldTypes()) {
      if (typeOrFunc instanceof Function) {
        if (typeOrFunc(field)) {
          return true
        }
      } else if (field.type === typeOrFunc) {
        return true
      }
    }
    return false
  }

  /**
   * Should return the component that will actually display the aggregation.
   */
  getComponent() {
    throw new Error(
      'Not implemented error. This aggregation should return a component.'
    )
  }

  getOrder() {
    return 50
  }

  /**
   * Compute the final aggregation value from the value sent by the server and the given
   * context.
   * @param {*} value is the value from the backend.
   * @param {object} context is an object containing data to describe the context of the
   *    aggregation.
   * @returns the final aggregation value for this type.
   */
  getValue(value, context) {
    return value
  }

  /**
   * @return object
   */
  serialize() {
    return {
      type: this.type,
      rawType: this.getRawType(),
      name: this.getName(),
    }
  }
}

export class EmptyCountViewAggregationType extends ViewAggregationType {
  static getType() {
    return 'empty_count'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewAggregationType.emptyCount')
  }

  getCompatibleFieldTypes() {
    return [() => true]
  }

  getComponent() {
    return GenericViewAggregation
  }
}

export class NotEmptyCountViewAggregationType extends ViewAggregationType {
  static getType() {
    return 'not_empty_count'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewAggregationType.notEmptyCount')
  }

  getCompatibleFieldTypes() {
    return [() => true]
  }

  getComponent() {
    return GenericViewAggregation
  }
}

export class EmptyPercentageViewAggregationType extends ViewAggregationType {
  static getType() {
    return 'empty_percentage'
  }

  getRawType() {
    return 'empty_count'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewAggregationType.emptyPercentage')
  }

  getShortName() {
    const { i18n } = this.app
    return i18n.t('viewAggregationType.emptyCount')
  }

  getCompatibleFieldTypes() {
    return [() => true]
  }

  getValue(value, context) {
    return `${Math.round((value / context.rowCount) * 100)}%`
  }

  getComponent() {
    return GenericViewAggregation
  }
}

export class NotEmptyPercentageViewAggregationType extends ViewAggregationType {
  static getType() {
    return 'not_empty_percentage'
  }

  getRawType() {
    return 'not_empty_count'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewAggregationType.notEmptyPercentage')
  }

  getShortName() {
    const { i18n } = this.app
    return i18n.t('viewAggregationType.notEmptyCount')
  }

  getCompatibleFieldTypes() {
    return [() => true]
  }

  getValue(value, context) {
    return `${Math.round((value / context.rowCount) * 100)}%`
  }

  getComponent() {
    return GenericViewAggregation
  }
}
