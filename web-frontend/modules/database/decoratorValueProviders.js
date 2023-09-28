import { Registerable } from '@baserow/modules/core/registry'

export class DecoratorValueProviderType extends Registerable {
  /**
   * A human readable name of the decorator provider type.
   */
  getName() {
    return null
  }

  /**
   * Returns a user description for this value provider.
   */
  getDescription() {}

  /**
   * The icon class name that is used as convenience for the user to
   * recognize certain valueProvider types. If you for example want the filter
   * icon, you must return 'filter' here. This will result in the classname
   * 'iconoir-filter'.
   */
  getIconClass() {
    return null
  }

  /**
   * Should return the view decorator type that the value provider is compatible with or
   * functions which take a view decoratorType and return a boolean indicating if the
   * value provider is compatible or not.
   *
   * You can also use a function like in this example:
   * [(decoratorType) => decoratorType.some_prop === 10, LeftBorderColorViewDecoratorType]
   * and then decoratorType which pass the test defined by the function will be
   * deemed as compatible.
   */
  getCompatibleDecoratorTypes() {
    return []
  }

  /**
   * Returns if a given view decoratorType is compatible with this value provider or
   * not.
   * Uses the list provided by `.getCompatibleDecoratorTypes()` to calculate this.
   */
  isCompatible(decorationType) {
    for (const typeOrFunc of this.getCompatibleDecoratorTypes()) {
      if (Object.prototype.hasOwnProperty.call(typeOrFunc, 'getType')) {
        if (decorationType.getType() === typeOrFunc.getType()) {
          return true
        }
      } else if (typeOrFunc instanceof Function) {
        if (typeOrFunc(decorationType)) {
          return true
        }
      }
    }
    return false
  }

  /**
   * Returns the component that allows the user to configure the value provider.
   * This component is responsible for creating the `value_provider_conf` object.
   *
   * If you want to reference fields in this object, you must use the key name
   * `field_id` to allow import/export to replace automatically any field id by the new
   * field id. `field_id`s can be anywhere in this object and this object can be as
   * deep as you need.
   */
  getFormComponent() {
    throw new Error(
      'Not implemented error. This value provider should return a component.'
    )
  }

  /**
   * Returns the default configuration when selecting this value provider from fields
   * and view
   * @returns the configuration object
   */
  getDefaultConfiguration({ fields, view }) {
    return {}
  }

  /**
   * Returns the value of this provider for the given row considering the configuration.
   *
   * @param {array} row the row
   * @param {object} options the configuration of the value provider
   * @param {array} fields the array of the fields of the current view
   *
   */
  getValue({ options, fields, row }) {
    throw new Error(
      'Not implemented error. This value provider should return a value.'
    )
  }

  getOrder() {
    return 50
  }

  /**
   * @return object
   */
  serialize() {
    return {
      type: this.type,
      name: this.getName(),
    }
  }
}
