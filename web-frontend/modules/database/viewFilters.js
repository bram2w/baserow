import { Registerable } from '@baserow/modules/core/registry'
import ViewFilterTypeText from '@baserow/modules/database/components/view/ViewFilterTypeText'
import ViewFilterTypeNumber from '@baserow/modules/database/components/view/ViewFilterTypeNumber'
import ViewFilterTypeSelectOptions from '@baserow/modules/database/components/view/ViewFilterTypeSelectOptions'
import ViewFilterTypeBoolean from '@baserow/modules/database/components/view/ViewFilterTypeBoolean'
import ViewFilterTypeDate from '@baserow/modules/database/components/view/ViewFilterTypeDate'
import { trueString } from '@baserow/modules/database/utils/constants'

export class ViewFilterType extends Registerable {
  /**
   * A human readable name of the view filter type.
   */
  getName() {
    return null
  }

  getExample() {
    return 'string'
  }

  constructor() {
    super()
    this.type = this.getType()
    this.name = this.getName()
    this.example = this.getExample()
    this.compatibleFieldTypes = this.getCompatibleFieldTypes()

    if (this.type === null) {
      throw new Error('The type name of a view type must be set.')
    }
    if (this.name === null) {
      throw new Error('The name of a view type must be set.')
    }
  }

  /**
   * @return object
   */
  serialize() {
    return {
      type: this.type,
      name: this.name,
      compatibleFieldTypes: this.compatibleFieldTypes,
    }
  }

  /**
   * Should return a component that is responsible for the filter's value. For example
   * for the equal filter a text field will be added where the user can enter whatever
   * he wants to filter on.
   */
  getInputComponent() {
    return null
  }

  /**
   * Optionally, right before updating the string value can be prepared. This could for
   * example be used to convert the value to a number.
   */
  prepareValue(value) {
    return value
  }

  /**
   * Should return the field type names that the filter is compatible with. So for
   * example ['text', 'long_text']. When that field is selected as filter it is only
   * possible to select compatible filter types. If no filters are compatible with a
   * field then that field will be disabled.
   */
  getCompatibleFieldTypes() {
    return []
  }

  /**
   * In order to real time check if the row applies to the filters we also need to
   * check on the web-frontend side if the value matches. Should return true if the
   * rowValue applies to the filterValue. This is really unfortunate in my opinion
   * because basically have the same code twice, but I could not think of an
   * alternative solution where we keep the real time check and we don't have
   * to wait for the server in order to tell us if the value matches.
   */
  matches(rowValue, filterValue, field, fieldType) {
    throw new Error('The matches method must be implemented for every filter.')
  }
}

export class EqualViewFilterType extends ViewFilterType {
  static getType() {
    return 'equal'
  }

  getName() {
    return 'is'
  }

  getInputComponent() {
    return ViewFilterTypeText
  }

  getCompatibleFieldTypes() {
    return ['text', 'long_text', 'url', 'email', 'number', 'phone_number']
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (rowValue === null) {
      rowValue = ''
    }

    rowValue = rowValue.toString().toLowerCase().trim()
    filterValue = filterValue.toString().toLowerCase().trim()
    return filterValue === '' || rowValue === filterValue
  }
}

export class NotEqualViewFilterType extends ViewFilterType {
  static getType() {
    return 'not_equal'
  }

  getName() {
    return 'is not'
  }

  getInputComponent() {
    return ViewFilterTypeText
  }

  getCompatibleFieldTypes() {
    return ['text', 'long_text', 'url', 'email', 'number', 'phone_number']
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (rowValue === null) {
      rowValue = ''
    }

    rowValue = rowValue.toString().toLowerCase().trim()
    filterValue = filterValue.toString().toLowerCase().trim()
    return filterValue === '' || rowValue !== filterValue
  }
}

export class FilenameContainsViewFilterType extends ViewFilterType {
  static getType() {
    return 'filename_contains'
  }

  getName() {
    return 'filename contains'
  }

  getInputComponent() {
    return ViewFilterTypeText
  }

  getCompatibleFieldTypes() {
    return ['file']
  }

  matches(rowValue, filterValue, field, fieldType) {
    return fieldType.containsFilter(rowValue, filterValue, field)
  }
}

export class ContainsViewFilterType extends ViewFilterType {
  static getType() {
    return 'contains'
  }

  getName() {
    return 'contains'
  }

  getInputComponent() {
    return ViewFilterTypeText
  }

  getCompatibleFieldTypes() {
    return [
      'text',
      'long_text',
      'url',
      'email',
      'phone_number',
      'date',
      'single_select',
      'number',
    ]
  }

  matches(rowValue, filterValue, field, fieldType) {
    return fieldType.containsFilter(rowValue, filterValue, field)
  }
}

export class ContainsNotViewFilterType extends ViewFilterType {
  static getType() {
    return 'contains_not'
  }

  getName() {
    return 'contains not'
  }

  getInputComponent() {
    return ViewFilterTypeText
  }

  getCompatibleFieldTypes() {
    return [
      'text',
      'long_text',
      'url',
      'email',
      'phone_number',
      'date',
      'single_select',
      'number',
    ]
  }

  matches(rowValue, filterValue, field, fieldType) {
    return fieldType.notContainsFilter(rowValue, filterValue, field)
  }
}

export class DateEqualViewFilterType extends ViewFilterType {
  static getType() {
    return 'date_equal'
  }

  getName() {
    return 'is date'
  }

  getExample() {
    return '2020-01-01'
  }

  getInputComponent() {
    return ViewFilterTypeDate
  }

  getCompatibleFieldTypes() {
    return ['date']
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (rowValue === null) {
      rowValue = ''
    }

    rowValue = rowValue.toString().toLowerCase().trim()
    rowValue = rowValue.slice(0, 10)

    return filterValue === '' || rowValue === filterValue
  }
}

export class DateNotEqualViewFilterType extends ViewFilterType {
  static getType() {
    return 'date_not_equal'
  }

  getName() {
    return 'is not date'
  }

  getExample() {
    return '2020-01-01'
  }

  getInputComponent() {
    return ViewFilterTypeDate
  }

  getCompatibleFieldTypes() {
    return ['date']
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (rowValue === null) {
      rowValue = ''
    }

    rowValue = rowValue.toString().toLowerCase().trim()
    rowValue = rowValue.slice(0, 10)

    return filterValue === '' || rowValue !== filterValue
  }
}

export class HigherThanViewFilterType extends ViewFilterType {
  static getType() {
    return 'higher_than'
  }

  getName() {
    return 'higher than'
  }

  getExample() {
    return '100'
  }

  getInputComponent() {
    return ViewFilterTypeNumber
  }

  getCompatibleFieldTypes() {
    return ['number']
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (filterValue === '') {
      return true
    }

    rowValue = parseFloat(rowValue)
    filterValue = parseFloat(filterValue)
    return !isNaN(rowValue) && !isNaN(filterValue) && rowValue > filterValue
  }
}

export class LowerThanViewFilterType extends ViewFilterType {
  static getType() {
    return 'lower_than'
  }

  getName() {
    return 'lower than'
  }

  getExample() {
    return '100'
  }

  getInputComponent() {
    return ViewFilterTypeNumber
  }

  getCompatibleFieldTypes() {
    return ['number']
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (filterValue === '') {
      return true
    }

    rowValue = parseFloat(rowValue)
    filterValue = parseFloat(filterValue)
    return !isNaN(rowValue) && !isNaN(filterValue) && rowValue < filterValue
  }
}

export class SingleSelectEqualViewFilterType extends ViewFilterType {
  static getType() {
    return 'single_select_equal'
  }

  getName() {
    return 'is'
  }

  getExample() {
    return '1'
  }

  getInputComponent() {
    return ViewFilterTypeSelectOptions
  }

  getCompatibleFieldTypes() {
    return ['single_select']
  }

  matches(rowValue, filterValue, field, fieldType) {
    return (
      filterValue === '' ||
      (rowValue !== null && rowValue.id === parseInt(filterValue))
    )
  }
}

export class SingleSelectNotEqualViewFilterType extends ViewFilterType {
  static getType() {
    return 'single_select_not_equal'
  }

  getName() {
    return 'is not'
  }

  getExample() {
    return '1'
  }

  getInputComponent() {
    return ViewFilterTypeSelectOptions
  }

  getCompatibleFieldTypes() {
    return ['single_select']
  }

  matches(rowValue, filterValue, field, fieldType) {
    return (
      filterValue === '' ||
      rowValue === null ||
      (rowValue !== null && rowValue.id !== parseInt(filterValue))
    )
  }
}

export class BooleanViewFilterType extends ViewFilterType {
  static getType() {
    return 'boolean'
  }

  getName() {
    return 'is'
  }

  getExample() {
    return 'true'
  }

  getInputComponent() {
    return ViewFilterTypeBoolean
  }

  getCompatibleFieldTypes() {
    return ['boolean']
  }

  matches(rowValue, filterValue, field, fieldType) {
    filterValue = trueString.includes(
      filterValue.toString().toLowerCase().trim()
    )
    rowValue = trueString.includes(rowValue.toString().toLowerCase().trim())
    return filterValue ? rowValue : !rowValue
  }
}

export class EmptyViewFilterType extends ViewFilterType {
  static getType() {
    return 'empty'
  }

  getName() {
    return 'is empty'
  }

  getExample() {
    return ''
  }

  prepareValue(value) {
    return ''
  }

  getCompatibleFieldTypes() {
    return [
      'text',
      'long_text',
      'url',
      'email',
      'number',
      'date',
      'boolean',
      'link_row',
      'file',
      'single_select',
      'phone_number',
    ]
  }

  matches(rowValue, filterValue, field, fieldType) {
    return (
      rowValue === null ||
      rowValue === [] ||
      rowValue === false ||
      rowValue.toString().trim() === ''
    )
  }
}

export class NotEmptyViewFilterType extends ViewFilterType {
  static getType() {
    return 'not_empty'
  }

  getName() {
    return 'is not empty'
  }

  getExample() {
    return ''
  }

  prepareValue(value) {
    return ''
  }

  getCompatibleFieldTypes() {
    return [
      'text',
      'long_text',
      'url',
      'email',
      'number',
      'date',
      'boolean',
      'link_row',
      'file',
      'single_select',
      'phone_number',
    ]
  }

  matches(rowValue, filterValue, field, fieldType) {
    return !(
      rowValue === null ||
      rowValue === [] ||
      rowValue === false ||
      rowValue.toString().trim() === ''
    )
  }
}
