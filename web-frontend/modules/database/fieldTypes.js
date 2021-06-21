import moment from 'moment'
import BigNumber from 'bignumber.js'

import {
  isValidURL,
  isValidEmail,
  isSimplePhoneNumber,
} from '@baserow/modules/core/utils/string'
import { Registerable } from '@baserow/modules/core/registry'

import FieldNumberSubForm from '@baserow/modules/database/components/field/FieldNumberSubForm'
import FieldTextSubForm from '@baserow/modules/database/components/field/FieldTextSubForm'
import FieldDateSubForm from '@baserow/modules/database/components/field/FieldDateSubForm'
import FieldLinkRowSubForm from '@baserow/modules/database/components/field/FieldLinkRowSubForm'
import FieldSingleSelectSubForm from '@baserow/modules/database/components/field/FieldSingleSelectSubForm'

import GridViewFieldText from '@baserow/modules/database/components/view/grid/fields/GridViewFieldText'
import GridViewFieldLongText from '@baserow/modules/database/components/view/grid/fields/GridViewFieldLongText'
import GridViewFieldURL from '@baserow/modules/database/components/view/grid/fields/GridViewFieldURL'
import GridViewFieldEmail from '@baserow/modules/database/components/view/grid/fields/GridViewFieldEmail'
import GridViewFieldLinkRow from '@baserow/modules/database/components/view/grid/fields/GridViewFieldLinkRow'
import GridViewFieldNumber from '@baserow/modules/database/components/view/grid/fields/GridViewFieldNumber'
import GridViewFieldBoolean from '@baserow/modules/database/components/view/grid/fields/GridViewFieldBoolean'
import GridViewFieldDate from '@baserow/modules/database/components/view/grid/fields/GridViewFieldDate'
import GridViewFieldFile from '@baserow/modules/database/components/view/grid/fields/GridViewFieldFile'
import GridViewFieldSingleSelect from '@baserow/modules/database/components/view/grid/fields/GridViewFieldSingleSelect'
import GridViewFieldPhoneNumber from '@baserow/modules/database/components/view/grid/fields/GridViewFieldPhoneNumber'

import FunctionalGridViewFieldText from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldText'
import FunctionalGridViewFieldLongText from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldLongText'
import FunctionalGridViewFieldLinkRow from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldLinkRow'
import FunctionalGridViewFieldNumber from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldNumber'
import FunctionalGridViewFieldBoolean from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldBoolean'
import FunctionalGridViewFieldDate from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldDate'
import FunctionalGridViewFieldFile from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldFile'
import FunctionalGridViewFieldSingleSelect from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldSingleSelect'
import FunctionalGridViewFieldPhoneNumber from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldPhoneNumber'

import RowEditFieldText from '@baserow/modules/database/components/row/RowEditFieldText'
import RowEditFieldLongText from '@baserow/modules/database/components/row/RowEditFieldLongText'
import RowEditFieldURL from '@baserow/modules/database/components/row/RowEditFieldURL'
import RowEditFieldEmail from '@baserow/modules/database/components/row/RowEditFieldEmail'
import RowEditFieldLinkRow from '@baserow/modules/database/components/row/RowEditFieldLinkRow'
import RowEditFieldNumber from '@baserow/modules/database/components/row/RowEditFieldNumber'
import RowEditFieldBoolean from '@baserow/modules/database/components/row/RowEditFieldBoolean'
import RowEditFieldDate from '@baserow/modules/database/components/row/RowEditFieldDate'
import RowEditFieldFile from '@baserow/modules/database/components/row/RowEditFieldFile'
import RowEditFieldSingleSelect from '@baserow/modules/database/components/row/RowEditFieldSingleSelect'
import RowEditFieldPhoneNumber from '@baserow/modules/database/components/row/RowEditFieldPhoneNumber'

import { trueString } from '@baserow/modules/database/utils/constants'
import {
  getDateMomentFormat,
  getTimeMomentFormat,
} from '@baserow/modules/database/utils/date'
import {
  filenameContainsFilter,
  genericContainsFilter,
} from '@baserow/modules/database/utils/fieldFilters'

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
   * This functional component should represent an unselect field cell related to the
   * value of this type. It will only be used in the grid view and is only for fast
   * displaying purposes, not for editing the value. This is because functional
   * components are much faster. When a user clicks on the cell it will be replaced
   * with the real component.
   */
  getFunctionalGridViewFieldComponent() {
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

  /**
   * Indicates if is possible for the field type to be the primary field.
   */
  getCanBePrimaryField() {
    return true
  }

  constructor() {
    super()
    this.type = this.getType()
    this.iconClass = this.getIconClass()
    this.name = this.getName()
    this.sortIndicator = this.getSortIndicator()
    this.canSortInView = this.getCanSortInView()
    this.canBePrimaryField = this.getCanBePrimaryField()

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
   * Should return a for humans readable representation of the value. This is for
   * example used by the link row field and row modal. This is not a problem with most
   * fields like text or number, but some store a more complex object object like
   * the single select or file field. In this case, the object might needs to be
   * converted to string.
   */
  toHumanReadableString(field, value) {
    return value || ''
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

  /**
   * Should return a string indicating which data type is expected. (e.g. string). The
   * value is shown in the documentation above the description.
   */
  getDocsDataType(field) {
    throw new Error('The docs data type must be set.')
  }

  /**
   * Should return a single line description explaining which value is expected for
   * the field. The value is shown in the overview of fields.
   */
  getDocsDescription(field) {
    throw new Error('The docs description must be set.')
  }

  /**
   * Should return an example value of the data. Will be shown in the request and
   * response examples.
   */
  getDocsRequestExample(field) {
    throw new Error('The docs example must be set.')
  }

  /**
   * If the response value differs from the accepted value as request then an
   * alternative can be provided here. By default the request example is returned
   * here.
   */
  getDocsResponseExample(field) {
    return this.getDocsRequestExample(field)
  }

  /**
   * Generate a field sample for the given field that is displayed in auto-doc.
   * @returns a sample for this field.
   */
  getDocsFieldResponseExample({
    id,
    table_id: tableId,
    name,
    order,
    type,
    primary,
  }) {
    return {
      id,
      table_id: tableId,
      name,
      order,
      type,
      primary,
    }
  }

  /**
   * Should return a contains filter function unique for this field type.
   */
  getContainsFilterFunction() {
    return (rowValue, humanReadableRowValue, filterValue) => false
  }

  /**
   * Converts rowValue to its human readable form first before applying the
   * filter returned from getContainsFilterFunction.
   */
  containsFilter(rowValue, filterValue, field) {
    return (
      filterValue === '' ||
      this.getContainsFilterFunction()(
        rowValue,
        this.toHumanReadableString(field, rowValue),
        filterValue
      )
    )
  }

  /**
   * Converts rowValue to its human readable form first before applying the field
   * filter returned by getContainsFilterFunction's notted.
   */
  notContainsFilter(rowValue, filterValue, field) {
    return (
      filterValue === '' ||
      !this.getContainsFilterFunction()(
        rowValue,
        this.toHumanReadableString(field, rowValue),
        filterValue
      )
    )
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
    return 'Single line text'
  }

  getFormComponent() {
    return FieldTextSubForm
  }

  getGridViewFieldComponent() {
    return GridViewFieldText
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldText
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

  getDocsDataType(field) {
    return 'string'
  }

  getDocsDescription(field) {
    return 'Accepts single line text.'
  }

  getDocsRequestExample(field) {
    return 'string'
  }

  getContainsFilterFunction() {
    return genericContainsFilter
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

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldLongText
  }

  getRowEditFieldComponent() {
    return RowEditFieldLongText
  }

  getEmptyValue(field) {
    return ''
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

  getDocsDataType(field) {
    return 'string'
  }

  getDocsDescription(field) {
    return 'Accepts multi line text.'
  }

  getDocsRequestExample(field) {
    return 'string'
  }

  getContainsFilterFunction() {
    return genericContainsFilter
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

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldLinkRow
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

  getCanBePrimaryField() {
    return false
  }

  prepareValueForCopy(field, value) {
    return JSON.stringify({
      tableId: field.link_row_table,
      value,
    })
  }

  prepareValueForPaste(field, clipboardData) {
    let values

    try {
      values = JSON.parse(clipboardData.getData('text'))
    } catch (SyntaxError) {
      return []
    }

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

  getDocsDataType(field) {
    return 'array'
  }

  getDocsDescription(field) {
    return (
      `Accepts an array containing the identifiers of the related rows from table ` +
      `${field.link_row_table}. All identifiers must be provided every time the ` +
      `relations are updated. If an empty array is provided all relations will be ` +
      `deleted.`
    )
  }

  getDocsRequestExample(field) {
    return [1]
  }

  getDocsResponseExample(field) {
    return [
      {
        id: 0,
        value: 'string',
      },
    ]
  }
}

export class NumberFieldType extends FieldType {
  static getMaxNumberLength() {
    return 50
  }

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

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldNumber
  }

  getRowEditFieldComponent() {
    return RowEditFieldNumber
  }

  getSortIndicator() {
    return ['text', '1', '9']
  }

  getSort(name, order) {
    return (a, b) => {
      if (a[name] === b[name]) {
        return 0
      }

      if (
        (a[name] === null && order === 'ASC') ||
        (b[name] === null && order === 'DESC')
      ) {
        return -1
      }

      if (
        (b[name] === null && order === 'ASC') ||
        (a[name] === null && order === 'DESC')
      ) {
        return 1
      }

      const numberA = new BigNumber(a[name])
      const numberB = new BigNumber(b[name])

      return order === 'ASC'
        ? numberA.isLessThan(numberB)
          ? -1
          : 1
        : numberB.isLessThan(numberA)
        ? -1
        : 1
    }
  }

  /**
   * First checks if the value is numeric, if that is the case, the number is going
   * to be formatted.
   */
  prepareValueForPaste(field, clipboardData) {
    const value = clipboardData.getData('text')
    if (
      isNaN(parseFloat(value)) ||
      !isFinite(value) ||
      value.split('.')[0].replace('-', '').length >
        NumberFieldType.getMaxNumberLength()
    ) {
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
    let number = new BigNumber(value)
    if (!field.number_negative && number.isLessThan(0)) {
      number = 0
    }
    return number.toFixed(decimalPlaces)
  }

  getDocsDataType(field) {
    return field.number_type === 'DECIMAL' ? 'decimal' : 'number'
  }

  getDocsDescription(field) {
    let description = 'Accepts a '

    if (!field.number_negative) {
      description += 'positive '
    }

    description +=
      field.number_type === 'DECIMAL'
        ? `decimal with ${field.number_decimal_places} places after the dot.`
        : 'number.'

    return description
  }

  getDocsRequestExample(field) {
    if (field.number_type === 'DECIMAL') {
      let number = '0.'
      for (let i = 1; i <= field.number_decimal_places; i++) {
        number += '0'
      }
      return number
    }
    return 0
  }

  getContainsFilterFunction() {
    return genericContainsFilter
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

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldBoolean
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

  getDocsDataType(field) {
    return 'boolean'
  }

  getDocsDescription(field) {
    return 'Accepts a boolean.'
  }

  getDocsRequestExample(field) {
    return true
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

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldDate
  }

  getRowEditFieldComponent() {
    return RowEditFieldDate
  }

  getSortIndicator() {
    return ['text', '1', '9']
  }

  getSort(name, order) {
    return (a, b) => {
      if (a[name] === b[name]) {
        return 0
      }

      if (
        (a[name] === null && order === 'ASC') ||
        (b[name] === null && order === 'DESC')
      ) {
        return -1
      }

      if (
        (b[name] === null && order === 'ASC') ||
        (a[name] === null && order === 'DESC')
      ) {
        return 1
      }

      const timeA = new Date(a[name]).getTime()
      const timeB = new Date(b[name]).getTime()

      return order === 'ASC' ? (timeA < timeB ? -1 : 1) : timeB < timeA ? -1 : 1
    }
  }

  toHumanReadableString(field, value) {
    const date = moment.utc(value)

    if (date.isValid()) {
      const dateFormat = getDateMomentFormat(field.date_format)
      let dateString = date.format(dateFormat)

      if (field.date_include_time) {
        const timeFormat = getTimeMomentFormat(field.date_time_format)
        dateString = `${dateString} ${date.format(timeFormat)}`
      }

      return dateString
    } else {
      return ''
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

  getDocsDataType(field) {
    return 'date'
  }

  getDocsDescription(field) {
    return field.date_include_time
      ? 'Accepts a date time in ISO format.'
      : 'Accepts a date in ISO format.'
  }

  getDocsRequestExample(field) {
    return field.date_include_time ? '2020-01-01T12:00:00Z' : '2020-01-01'
  }

  getContainsFilterFunction() {
    return genericContainsFilter
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

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldText
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

  getDocsDataType(field) {
    return 'string'
  }

  getDocsDescription(field) {
    return 'Accepts a string that must be a URL.'
  }

  getDocsRequestExample(field) {
    return 'https://baserow.io'
  }

  getContainsFilterFunction() {
    return genericContainsFilter
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

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldText
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

  getDocsDataType(field) {
    return 'string'
  }

  getDocsDescription(field) {
    return 'Accepts a string that must be an email address.'
  }

  getDocsRequestExample(field) {
    return 'example@baserow.io'
  }

  getContainsFilterFunction() {
    return genericContainsFilter
  }
}

export class FileFieldType extends FieldType {
  static getType() {
    return 'file'
  }

  getIconClass() {
    return 'file'
  }

  getName() {
    return 'File'
  }

  getGridViewFieldComponent() {
    return GridViewFieldFile
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldFile
  }

  getRowEditFieldComponent() {
    return RowEditFieldFile
  }

  toHumanReadableString(field, value) {
    return value.map((file) => file.visible_name).join(', ')
  }

  prepareValueForCopy(field, value) {
    return JSON.stringify(value)
  }

  prepareValueForPaste(field, clipboardData) {
    let value

    try {
      value = JSON.parse(clipboardData.getData('text'))
    } catch (SyntaxError) {
      return []
    }

    if (!Array.isArray(value)) {
      return []
    }
    // Each object should at least have the file name as property.
    for (let i = 0; i < value.length; i++) {
      if (!Object.prototype.hasOwnProperty.call(value[i], 'name')) {
        return []
      }
    }
    return value
  }

  getEmptyValue(field) {
    return []
  }

  getCanSortInView() {
    return false
  }

  getDocsDataType() {
    return 'array'
  }

  getDocsDescription() {
    return 'Accepts an array of objects containing at least the name of the user file.'
  }

  getDocsRequestExample() {
    return [
      {
        name:
          'VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png',
      },
    ]
  }

  getDocsResponseExample() {
    return [
      {
        url:
          'https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png',
        thumbnails: {
          tiny: {
            url:
              'https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png',
            width: 21,
            height: 21,
          },
          small: {
            url:
              'https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png',
            width: 48,
            height: 48,
          },
        },
        name:
          'VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png',
        size: 229940,
        mime_type: 'image/png',
        is_image: true,
        image_width: 1280,
        image_height: 585,
        uploaded_at: '2020-11-17T12:16:10.035234+00:00',
      },
    ]
  }

  getContainsFilterFunction() {
    return filenameContainsFilter
  }
}

export class SingleSelectFieldType extends FieldType {
  static getType() {
    return 'single_select'
  }

  getIconClass() {
    return 'chevron-circle-down '
  }

  getName() {
    return 'Single select'
  }

  getFormComponent() {
    return FieldSingleSelectSubForm
  }

  getGridViewFieldComponent() {
    return GridViewFieldSingleSelect
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldSingleSelect
  }

  getRowEditFieldComponent() {
    return RowEditFieldSingleSelect
  }

  getSort(name, order) {
    return (a, b) => {
      const stringA = a[name] === null ? '' : '' + a[name].value
      const stringB = b[name] === null ? '' : '' + b[name].value

      return order === 'ASC'
        ? stringA.localeCompare(stringB)
        : stringB.localeCompare(stringA)
    }
  }

  prepareValueForUpdate(field, value) {
    if (value === undefined || value === null) {
      return null
    }
    return value.id
  }

  prepareValueForCopy(field, value) {
    if (value === undefined || value === null) {
      return ''
    }
    return value.id
  }

  prepareValueForPaste(field, clipboardData) {
    const value = parseInt(clipboardData.getData('text'))

    for (let i = 0; i <= field.select_options.length; i++) {
      const option = field.select_options[i]
      if (option.id === value) {
        return option
      }
    }
  }

  toHumanReadableString(field, value) {
    if (value === undefined || value === null) {
      return ''
    }
    return value.value
  }

  getDocsDataType() {
    return 'integer'
  }

  getDocsDescription(field) {
    const options = field.select_options
      .map(
        (option) =>
          // @TODO move this template to a component.
          `<div class="select-options-listing">
              <div class="select-options-listing__id">${option.id}</div>
              <div class="select-options-listing__value background-color--${option.color}">${option.value}</div>
           </div>
          `
      )
      .join('\n')

    return `
      Accepts an integer representing the chosen select option id or null if none is selected.
      <br />
      ${options}
    `
  }

  getDocsRequestExample() {
    return 1
  }

  getDocsResponseExample() {
    return {
      id: 1,
      value: 'Option',
      color: 'light-blue',
    }
  }

  getContainsFilterFunction() {
    return genericContainsFilter
  }
}

export class PhoneNumberFieldType extends FieldType {
  static getType() {
    return 'phone_number'
  }

  getIconClass() {
    return 'phone'
  }

  getName() {
    return 'Phone Number'
  }

  getGridViewFieldComponent() {
    return GridViewFieldPhoneNumber
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldPhoneNumber
  }

  getRowEditFieldComponent() {
    return RowEditFieldPhoneNumber
  }

  prepareValueForPaste(field, clipboardData) {
    const value = clipboardData.getData('text')
    return isSimplePhoneNumber(value) ? value : ''
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

  getSortIndicator() {
    return ['text', '0', '9']
  }

  getDocsDataType(field) {
    return 'string'
  }

  getDocsDescription(field) {
    return (
      'Accepts a phone number which has a maximum length of 100 characters' +
      ' consisting solely of digits, spaces and the following characters: ' +
      'Nx,._+*()#=;/- .'
    )
  }

  getDocsRequestExample(field) {
    return '+1-541-754-3010'
  }

  getContainsFilterFunction() {
    return genericContainsFilter
  }
}
