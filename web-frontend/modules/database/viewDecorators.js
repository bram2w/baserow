import { Registerable } from '@baserow/modules/core/registry'

export class ViewDecoratorType extends Registerable {
  /**
   * A human readable name of the decorator type.
   */
  getName() {
    return null
  }

  /**
   * A description of the decorator type.
   */
  getDescription() {
    return null
  }

  /**
   * @returns the image URL to illustrate this decorator.
   */
  getImage() {
    return null
  }

  /**
   * If the decorator type is disabled, this text will be visible explaining why.
   */
  getDeactivatedText({ view }) {}

  /**
   * When the deactivated view decorator is clicked, this modal will be shown.
   */
  getDeactivatedClickModal() {
    return null
  }

  /**
   * Indicates if the decorator type is disabled.
   */
  isDeactivated(workspaceId) {
    return false
  }

  /**
   * Returns whether or not the user can add a new instance of this decorator.
   * A decorator might be disabled if, for example, there is already one occurrence
   * of the same type for the view.
   * The result must be an array. The first item is a boolean value, `true` if
   * the decorator is enabled. If not, it should be `false` and the second item
   * must be a user string describing the reason why it's not available.
   */
  canAdd({ view }) {
    return [false, '']
  }

  /**
   * Returns whether or not a given viewType is compatible with this view decorator.
   */
  isCompatible(view) {
    return false
  }

  /**
   * Should return the component that will actually decorate the record.
   */
  getComponent() {
    throw new Error(
      'Not implemented error. This view decorator should return a component.'
    )
  }

  /**
   * Returns the place where the decorator should appears. Allowed values are:
   * - `wrapper` if the decorator is a wrapper of the record.
   * - `first_cell` to decorate the first cell.
   */
  getPlace() {
    return null
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
