import { Registerable } from '@baserow/modules/core/registry'

import FieldNumberSubForm from '@baserow/modules/database/components/field/FieldNumberSubForm'
import FieldTextSubForm from '@baserow/modules/database/components/field/FieldTextSubForm'

import GridViewFieldText from '@baserow/modules/database/components/view/grid/GridViewFieldText'
import GridViewFieldNumber from '@baserow/modules/database/components/view/grid/GridViewFieldNumber'
import GridViewFieldBoolean from '@baserow/modules/database/components/view/grid/GridViewFieldBoolean'

import RowEditFieldText from '@baserow/modules/database/components/row/RowEditFieldText'
import RowEditFieldNumber from '@baserow/modules/database/components/row/RowEditFieldNumber'
import RowEditFieldBoolean from '@baserow/modules/database/components/row/RowEditFieldBoolean'

export class FieldType extends Registerable {
  /**
   * The font awesome 5 icon name that is used as convenience for the user to
   * recognize certain view types. If you for example want the database
   * icon, you must return 'database' here. This will result in the classname
   * 'fas fa-database'.
   */
  getIconClass() {
    return null
  }

  /**
   * A human readable name of the view type.
   */
  getName() {
    return null
  }

  /**
   * The form component will be added to the field type context component if the
   * matching type is selected. This component is used to create and update
   * fields and should contain the unique inputs needed for this type. For
   * example if we are creating a number fields this component should contain
   * the inputs to choose of it is an integer of decimal.
   */
  getFormComponent() {
    return null
  }

  /**
   * This grid view field component should represent the related row value of this
   * type. It will only be used in the grid view and it also responsible for editing
   * the value.
   */
  getGridViewFieldComponent() {
    throw new Error(
      'Not implement error. This method should return a component.'
    )
  }

  /**
   * The row edit field should represent a the related row value of this type. It
   * will be used in the row edit modal, but can also be used in other forms. It is
   * responsible for editing the value.
   */
  getRowEditFieldComponent() {
    throw new Error(
      'Not implement error. This method should return a component.'
    )
  }

  /**
   * Because we want to show a new row immediately after creating we need to have an
   * empty value to show right away.
   */
  getEmptyValue(field) {
    return null
  }

  constructor() {
    super()
    this.type = this.getType()
    this.iconClass = this.getIconClass()
    this.name = this.getName()

    if (this.type === null) {
      throw new Error('The type name of a view type must be set.')
    }
    if (this.iconClass === null) {
      throw new Error('The icon class of a view type must be set.')
    }
    if (this.name === null) {
      throw new Error('The name of a view type must be set.')
    }
  }

  /**
   * Every time a fresh field object is fetched from the backend, it will be
   * populated, this is the moment to update some values. Because each view type
   * can have unique properties, they might need to be populated. This method
   * can be overwritten in order the populate the correct values.
   */
  populate(field) {
    return field
  }

  /**
   * @return object
   */
  serialize() {
    return {
      type: this.type,
      iconClass: this.iconClass,
      name: this.name,
    }
  }

  /**
   * Should return a for humans readable representation of the value.
   */
  toHumanReadableString(field, value) {
    return value
  }
}

export class TextFieldType extends FieldType {
  static getType() {
    return 'text'
  }

  getIconClass() {
    return 'font'
  }

  getName() {
    return 'Text'
  }

  getFormComponent() {
    return FieldTextSubForm
  }

  getGridViewFieldComponent() {
    return GridViewFieldText
  }

  getRowEditFieldComponent() {
    return RowEditFieldText
  }

  getEmptyValue(field) {
    return field.text_default
  }
}

export class NumberFieldType extends FieldType {
  static getType() {
    return 'number'
  }

  getIconClass() {
    return 'hashtag'
  }

  getName() {
    return 'Number'
  }

  getFormComponent() {
    return FieldNumberSubForm
  }

  getGridViewFieldComponent() {
    return GridViewFieldNumber
  }

  getRowEditFieldComponent() {
    return RowEditFieldNumber
  }
}

export class BooleanFieldType extends FieldType {
  static getType() {
    return 'boolean'
  }

  getIconClass() {
    return 'check-square'
  }

  getName() {
    return 'Boolean'
  }

  getGridViewFieldComponent() {
    return GridViewFieldBoolean
  }

  getRowEditFieldComponent() {
    return RowEditFieldBoolean
  }

  getEmptyValue(field) {
    return false
  }
}
