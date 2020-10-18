import moment from 'moment'

import { isValidURL, isValidEmail } from '@baserow/modules/core/utils/string'
import { Registerable } from '@baserow/modules/core/registry'

import FieldNumberSubForm from '@baserow/modules/database/components/field/FieldNumberSubForm'
import FieldTextSubForm from '@baserow/modules/database/components/field/FieldTextSubForm'
import FieldDateSubForm from '@baserow/modules/database/components/field/FieldDateSubForm'
import FieldLinkRowSubForm from '@baserow/modules/database/components/field/FieldLinkRowSubForm'

import GridViewFieldText from '@baserow/modules/database/components/view/grid/GridViewFieldText'
import GridViewFieldLongText from '@baserow/modules/database/components/view/grid/GridViewFieldLongText'
import GridViewFieldURL from '@baserow/modules/database/components/view/grid/GridViewFieldURL'
import GridViewFieldEmail from '@baserow/modules/database/components/view/grid/GridViewFieldEmail'
import GridViewFieldLinkRow from '@baserow/modules/database/components/view/grid/GridViewFieldLinkRow'
import GridViewFieldNumber from '@baserow/modules/database/components/view/grid/GridViewFieldNumber'
import GridViewFieldBoolean from '@baserow/modules/database/components/view/grid/GridViewFieldBoolean'
import GridViewFieldDate from '@baserow/modules/database/components/view/grid/GridViewFieldDate'

import RowEditFieldText from '@baserow/modules/database/components/row/RowEditFieldText'
import RowEditFieldLongText from '@baserow/modules/database/components/row/RowEditFieldLongText'
import RowEditFieldURL from '@baserow/modules/database/components/row/RowEditFieldURL'
import RowEditFieldEmail from '@baserow/modules/database/components/row/RowEditFieldEmail'
import RowEditFieldLinkRow from '@baserow/modules/database/components/row/RowEditFieldLinkRow'
import RowEditFieldNumber from '@baserow/modules/database/components/row/RowEditFieldNumber'
import RowEditFieldBoolean from '@baserow/modules/database/components/row/RowEditFieldBoolean'
import RowEditFieldDate from '@baserow/modules/database/components/row/RowEditFieldDate'

import { trueString } from '@baserow/modules/database/utils/constants'

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

  /**
   * Indicates whether or not it is possible to sort in a view.
   */
  getCanSortInView() {
    return true
  }

  constructor() {
    super()
    this.type = this.getType()
    this.iconClass = this.getIconClass()
    this.name = this.getName()
    this.sortIndicator = this.getSortIndicator()
    this.canSortInView = this.getCanSortInView()

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
      sortIndicator: this.sortIndicator,
      canSortInView: this.canSortInView,
    }
  }

  /**
   * Should return a for humans readable representation of the value.
   */
  toHumanReadableString(field, value) {
    return value
  }

  /**
   * Should return a sort function that is unique for the field type.
   */
  getSort() {
    throw new Error(
      'Not implement error. This method should by a sort function.'
    )
  }

  /**
   * Should return a visualisation of how the sort function is going to work. For
   * example ['text', 'A', 'Z'] will result in 'A -> Z' as ascending and 'Z -> A'
   * descending visualisation for the user. It is also possible to use a Font Awesome
   * icon here by changing the first value to 'icon'. For example
   * ['icon', 'square', 'check-square'].
   */
  getSortIndicator() {
    return ['text', 'A', 'Z']
  }

  /**
   * This hook is called before the field's value is copied to the clipboard.
   * Optionally formatting can be done here. By default the value is always
   * converted to a string.
   */
  prepareValueForCopy(field, value) {
    return value.toString()
  }

  /**
   * This hook is called before the field's value is overwritten by the clipboard
   * data. That data might needs to be prepared so that the field accepts it.
   * By default the text value if the clipboard data is used.
   */
  prepareValueForPaste(field, clipboardData) {
    return clipboardData.getData('text')
  }

  /**
   * Optionally the value can be prepared just before the update API call is being
   * made. The new value is not going to saved in the store it is just for preparing
   * the value such that it fits the requirements of the API endpoint.
   */
  prepareValueForUpdate(field, value) {
    return value
  }

  /**
   * A hook that is called when a table is deleted. Some fields depend on other tables
   * than the table that they belong to. So action might be required when that table
   * is deleted.
   */
  tableDeleted(context, field, table, database) {}
}

export class TextFieldType extends FieldType {
  static getType() {
    return 'text'
  }

  getIconClass() {
    return 'font'
  }

  getName() {
    return 'Single line text'
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

  getSort(name, order) {
    return (a, b) => {
      const stringA = a[name] === null ? '' : '' + a[name]
      const stringB = b[name] === null ? '' : '' + b[name]

      return order === 'ASC'
        ? stringA.localeCompare(stringB)
        : stringB.localeCompare(stringA)
    }
  }
}

export class LongTextFieldType extends FieldType {
  static getType() {
    return 'long_text'
  }

  getIconClass() {
    return 'align-left'
  }

  getName() {
    return 'Long text'
  }

  getGridViewFieldComponent() {
    return GridViewFieldLongText
  }

  getRowEditFieldComponent() {
    return RowEditFieldLongText
  }

  getSort(name, order) {
    return (a, b) => {
      const stringA = a[name] === null ? '' : '' + a[name]
      const stringB = b[name] === null ? '' : '' + b[name]

      return order === 'ASC'
        ? stringA.localeCompare(stringB)
        : stringB.localeCompare(stringA)
    }
  }
}

export class LinkRowFieldType extends FieldType {
  static getType() {
    return 'link_row'
  }

  getIconClass() {
    return 'plug'
  }

  getName() {
    return 'Link to table'
  }

  getFormComponent() {
    return FieldLinkRowSubForm
  }

  getGridViewFieldComponent() {
    return GridViewFieldLinkRow
  }

  getRowEditFieldComponent() {
    return RowEditFieldLinkRow
  }

  getEmptyValue(field) {
    return []
  }

  getCanSortInView() {
    return false
  }

  prepareValueForCopy(field, value) {
    return JSON.stringify({
      tableId: field.link_row_table,
      value,
    })
  }

  prepareValueForPaste(field, clipboardData) {
    const values = JSON.parse(clipboardData.getData('text'))
    if (field.link_row_table === values.tableId) {
      return values.value
    }
    return []
  }

  /**
   * The structure for updating is slightly different than what we need for displaying
   * the value because the display value does not have to be included. Here we convert
   * the array[object] structure to an array[id] structure.
   */
  prepareValueForUpdate(field, value) {
    return value.map((item) => (typeof item === 'object' ? item.id : item))
  }

  /**
   * When a table is deleted it might be the case that this is the related table of
   * the field. If so it means that this field has already been deleted and it needs
   * to be removed from the store without making an API call.
   */
  tableDeleted({ dispatch }, field, table, database) {
    if (field.link_row_table === table.id) {
      dispatch('field/forceDelete', field, { root: true })
    }
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

  getSortIndicator() {
    return ['text', '1', '9']
  }

  getSort(name, order) {
    return (a, b) => {
      const numberA = parseFloat(a[name])
      const numberB = parseFloat(b[name])

      if (isNaN(numberA) || isNaN(numberB)) {
        return -1
      }

      return order === 'ASC' ? numberA - numberB : numberB - numberA
    }
  }

  /**
   * First checks if the value is numeric, if that is the case, the number is going
   * to be formatted.
   */
  prepareValueForPaste(field, clipboardData) {
    const value = clipboardData.getData('text')
    if (isNaN(parseFloat(value)) || !isFinite(value)) {
      return null
    }
    return this.constructor.formatNumber(field, value)
  }

  /**
   * Formats the value based on the field's settings. The number will be rounded
   * if to much decimal places are provided and if negative numbers aren't allowed
   * they will be set to 0.
   */
  static formatNumber(field, value) {
    if (value === '' || isNaN(value) || value === undefined || value === null) {
      return null
    }
    const decimalPlaces =
      field.number_type === 'DECIMAL' ? field.number_decimal_places : 0
    let number = parseFloat(value)
    if (!field.number_negative && number < 0) {
      number = 0
    }
    return number.toFixed(decimalPlaces)
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

  getSortIndicator() {
    return ['icon', 'square', 'check-square']
  }

  getSort(name, order) {
    return (a, b) => {
      const intA = +a[name]
      const intB = +b[name]
      return order === 'ASC' ? intA - intB : intB - intA
    }
  }

  /**
   * Check if the clipboard data text contains a string that might indicate if the
   * value is true.
   */
  prepareValueForPaste(field, clipboardData) {
    const value = clipboardData.getData('text').toLowerCase().trim()
    return trueString.includes(value)
  }
}

export class DateFieldType extends FieldType {
  static getType() {
    return 'date'
  }

  getIconClass() {
    return 'calendar-alt'
  }

  getName() {
    return 'Date'
  }

  getFormComponent() {
    return FieldDateSubForm
  }

  getGridViewFieldComponent() {
    return GridViewFieldDate
  }

  getRowEditFieldComponent() {
    return RowEditFieldDate
  }

  getSortIndicator() {
    return ['text', '1', '9']
  }

  getSort(name, order) {
    return (a, b) => {
      if (a[name] === null || b[name] === null) {
        return -1
      }

      const timeA = new Date(a[name]).getTime()
      const timeB = new Date(b[name]).getTime()
      return order === 'ASC' ? timeA - timeB : timeB - timeA
    }
  }

  /**
   * Tries to parse the clipboard text value with moment and returns the date in the
   * correct format for the field. If it can't be parsed null is returned.
   */
  prepareValueForPaste(field, clipboardData) {
    const value = clipboardData.getData('text').toUpperCase()
    const date = moment.utc(value)

    if (date.isValid()) {
      return field.date_include_time ? date.format() : date.format('YYYY-MM-DD')
    } else {
      return null
    }
  }
}

export class URLFieldType extends FieldType {
  static getType() {
    return 'url'
  }

  getIconClass() {
    return 'link'
  }

  getName() {
    return 'URL'
  }

  getGridViewFieldComponent() {
    return GridViewFieldURL
  }

  getRowEditFieldComponent() {
    return RowEditFieldURL
  }

  prepareValueForPaste(field, clipboardData) {
    const value = clipboardData.getData('text')
    return isValidURL(value) ? value : ''
  }

  getSort(name, order) {
    return (a, b) => {
      const stringA = a[name] === null ? '' : '' + a[name]
      const stringB = b[name] === null ? '' : '' + b[name]

      return order === 'ASC'
        ? stringA.localeCompare(stringB)
        : stringB.localeCompare(stringA)
    }
  }
}

export class EmailFieldType extends FieldType {
  static getType() {
    return 'email'
  }

  getIconClass() {
    return 'at'
  }

  getName() {
    return 'Email'
  }

  getGridViewFieldComponent() {
    return GridViewFieldEmail
  }

  getRowEditFieldComponent() {
    return RowEditFieldEmail
  }

  prepareValueForPaste(field, clipboardData) {
    const value = clipboardData.getData('text')
    return isValidEmail(value) ? value : ''
  }

  getSort(name, order) {
    return (a, b) => {
      const stringA = a[name] === null ? '' : '' + a[name]
      const stringB = b[name] === null ? '' : '' + b[name]

      return order === 'ASC'
        ? stringA.localeCompare(stringB)
        : stringB.localeCompare(stringA)
    }
  }
}
