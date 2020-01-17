import FieldNumberSubForm from '@/modules/database/components/field/FieldNumberSubForm'
import FieldTextSubForm from '@/modules/database/components/field/FieldTextSubForm'

export class FieldType {
  /**
   * Must return a string with the unique name, this must be the same as the
   * type used in the backend.
   */
  getType() {
    return null
  }

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

  constructor() {
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
      name: this.name
    }
  }
}

export class TextFieldType extends FieldType {
  static getType() {
    return 'text'
  }

  getType() {
    return TextFieldType.getType()
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
}

export class NumberFieldType extends FieldType {
  static getType() {
    return 'number'
  }

  getType() {
    return NumberFieldType.getType()
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
}

export class BooleanFieldType extends FieldType {
  static getType() {
    return 'boolean'
  }

  getType() {
    return BooleanFieldType.getType()
  }

  getIconClass() {
    return 'check-square'
  }

  getName() {
    return 'Boolean'
  }
}
