import BigNumber from 'bignumber.js'

import moment from '@baserow/modules/core/moment'
import {
  isNumeric,
  isSimplePhoneNumber,
  isValidEmail,
  isValidURL,
  getFilenameFromUrl,
} from '@baserow/modules/core/utils/string'
import { Registerable } from '@baserow/modules/core/registry'

import FieldNumberSubForm from '@baserow/modules/database/components/field/FieldNumberSubForm'
import FieldRatingSubForm from '@baserow/modules/database/components/field/FieldRatingSubForm'
import FieldTextSubForm from '@baserow/modules/database/components/field/FieldTextSubForm'
import FieldDateSubForm from '@baserow/modules/database/components/field/FieldDateSubForm'
import FieldCreatedOnLastModifiedSubForm from '@baserow/modules/database/components/field/FieldCreatedOnLastModifiedSubForm'
import FieldLinkRowSubForm from '@baserow/modules/database/components/field/FieldLinkRowSubForm'
import FieldSelectOptionsSubForm from '@baserow/modules/database/components/field/FieldSelectOptionsSubForm'

import GridViewFieldText from '@baserow/modules/database/components/view/grid/fields/GridViewFieldText'
import GridViewFieldLongText from '@baserow/modules/database/components/view/grid/fields/GridViewFieldLongText'
import GridViewFieldURL from '@baserow/modules/database/components/view/grid/fields/GridViewFieldURL'
import GridViewFieldEmail from '@baserow/modules/database/components/view/grid/fields/GridViewFieldEmail'
import GridViewFieldLinkRow from '@baserow/modules/database/components/view/grid/fields/GridViewFieldLinkRow'
import GridViewFieldNumber from '@baserow/modules/database/components/view/grid/fields/GridViewFieldNumber'
import GridViewFieldRating from '@baserow/modules/database/components/view/grid/fields/GridViewFieldRating'
import GridViewFieldBoolean from '@baserow/modules/database/components/view/grid/fields/GridViewFieldBoolean'
import GridViewFieldDate from '@baserow/modules/database/components/view/grid/fields/GridViewFieldDate'
import GridViewFieldDateReadOnly from '@baserow/modules/database/components/view/grid/fields/GridViewFieldDateReadOnly'
import GridViewFieldFile from '@baserow/modules/database/components/view/grid/fields/GridViewFieldFile'
import GridViewFieldSingleSelect from '@baserow/modules/database/components/view/grid/fields/GridViewFieldSingleSelect'
import GridViewFieldMultipleSelect from '@baserow/modules/database/components/view/grid/fields/GridViewFieldMultipleSelect'
import GridViewFieldPhoneNumber from '@baserow/modules/database/components/view/grid/fields/GridViewFieldPhoneNumber'
import GridViewFieldMultipleCollaborators from '@baserow/modules/database/components/view/grid/fields/GridViewFieldMultipleCollaborators'

import FunctionalGridViewFieldText from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldText'
import FunctionalGridViewFieldLongText from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldLongText'
import FunctionalGridViewFieldLinkRow from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldLinkRow'
import FunctionalGridViewFieldNumber from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldNumber'
import FunctionalGridViewFieldRating from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldRating'
import FunctionalGridViewFieldBoolean from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldBoolean'
import FunctionalGridViewFieldDate from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldDate'
import FunctionalGridViewFieldFile from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldFile'
import FunctionalGridViewFieldSingleSelect from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldSingleSelect'
import FunctionalGridViewFieldMultipleSelect from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldMultipleSelect'
import FunctionalGridViewFieldFormula from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldFormula'
import FunctionalGridViewFieldMultipleCollaborators from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldMultipleCollaborators'
import FunctionalGridViewFieldURL from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldURL'

import RowEditFieldText from '@baserow/modules/database/components/row/RowEditFieldText'
import RowEditFieldLongText from '@baserow/modules/database/components/row/RowEditFieldLongText'
import RowEditFieldURL from '@baserow/modules/database/components/row/RowEditFieldURL'
import RowEditFieldEmail from '@baserow/modules/database/components/row/RowEditFieldEmail'
import RowEditFieldLinkRow from '@baserow/modules/database/components/row/RowEditFieldLinkRow'
import RowEditFieldNumber from '@baserow/modules/database/components/row/RowEditFieldNumber'
import RowEditFieldRating from '@baserow/modules/database/components/row/RowEditFieldRating'
import RowEditFieldBoolean from '@baserow/modules/database/components/row/RowEditFieldBoolean'
import RowEditFieldDate from '@baserow/modules/database/components/row/RowEditFieldDate'
import RowEditFieldDateReadOnly from '@baserow/modules/database/components/row/RowEditFieldDateReadOnly'
import RowEditFieldFile from '@baserow/modules/database/components/row/RowEditFieldFile'
import RowEditFieldSingleSelect from '@baserow/modules/database/components/row/RowEditFieldSingleSelect'
import RowEditFieldMultipleSelect from '@baserow/modules/database/components/row/RowEditFieldMultipleSelect'
import RowEditFieldPhoneNumber from '@baserow/modules/database/components/row/RowEditFieldPhoneNumber'
import RowEditFieldMultipleCollaborators from '@baserow/modules/database/components/row/RowEditFieldMultipleCollaborators'

import RowCardFieldBoolean from '@baserow/modules/database/components/card/RowCardFieldBoolean'
import RowCardFieldDate from '@baserow/modules/database/components/card/RowCardFieldDate'
import RowCardFieldEmail from '@baserow/modules/database/components/card/RowCardFieldEmail'
import RowCardFieldFile from '@baserow/modules/database/components/card/RowCardFieldFile'
import RowCardFieldFormula from '@baserow/modules/database/components/card/RowCardFieldFormula'
import RowCardFieldLinkRow from '@baserow/modules/database/components/card/RowCardFieldLinkRow'
import RowCardFieldMultipleSelect from '@baserow/modules/database/components/card/RowCardFieldMultipleSelect'
import RowCardFieldNumber from '@baserow/modules/database/components/card/RowCardFieldNumber'
import RowCardFieldRating from '@baserow/modules/database/components/card/RowCardFieldRating'
import RowCardFieldPhoneNumber from '@baserow/modules/database/components/card/RowCardFieldPhoneNumber'
import RowCardFieldSingleSelect from '@baserow/modules/database/components/card/RowCardFieldSingleSelect'
import RowCardFieldText from '@baserow/modules/database/components/card/RowCardFieldText'
import RowCardFieldURL from '@baserow/modules/database/components/card/RowCardFieldURL'
import RowCardFieldMultipleCollaborators from '@baserow/modules/database/components/card/RowCardFieldMultipleCollaborators'

import FormViewFieldLinkRow from '@baserow/modules/database/components/view/form/FormViewFieldLinkRow'

import { trueString } from '@baserow/modules/database/utils/constants'
import {
  getDateMomentFormat,
  getTimeMomentFormat,
} from '@baserow/modules/database/utils/date'
import {
  filenameContainsFilter,
  genericContainsFilter,
} from '@baserow/modules/database/utils/fieldFilters'
import GridViewFieldFormula from '@baserow/modules/database/components/view/grid/fields/GridViewFieldFormula'
import FieldFormulaSubForm from '@baserow/modules/database/components/field/FieldFormulaSubForm'
import FieldLookupSubForm from '@baserow/modules/database/components/field/FieldLookupSubForm'
import RowEditFieldFormula from '@baserow/modules/database/components/row/RowEditFieldFormula'
import ViewService from '@baserow/modules/database/services/view'
import FormService from '@baserow/modules/database/services/view/form'
import { UploadFileUserFileUploadType } from '@baserow/modules/core/userFileUploadTypes'

export class FieldType extends Registerable {
  /**
   * The font awesome 5 icon name that is used as convenience for the user to
   * recognize certain field types. If you for example want the database
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
   * By default the row edit field component is used in the form. This can
   * optionally be another component if needed. If null is returned, then the field
   * is marked as not compatible with the form view.
   */
  getFormViewFieldComponent() {
    return this.getRowEditFieldComponent()
  }

  /*
   * Optional properties for the FormViewFieldComponent
   */
  getFormViewFieldComponentProperties(context) {
    return {}
  }

  /**
   * This component should represent the field's value in a row card display. To
   * improve performance, this component should be a functional component.
   */
  getCardComponent() {
    throw new Error(
      'Not implement error. This method should return a component.'
    )
  }

  /**
   * In some cases, for example with the kanban view or the gallery view, we want to
   * only show the visible cards. In order to calculate the correct position of
   * those cards, we need to know the height. Because every field could have a
   * different height in the card, it must be returned here.
   */
  getCardValueHeight(field) {
    return this.getCardComponent().height || 0
  }

  /**
   * Because we want to show a new row immediately after creating we need to have an
   * empty value to show right away.
   */
  getEmptyValue(field) {
    return null
  }

  /**
   * Should return true if the provided value is empty.
   */
  isEmpty(field, value) {
    if (Array.isArray(value) && value.length === 0) {
      return true
    }
    if (typeof val === 'object' && Object.keys(value).length === 0) {
      return true
    }
    return [null, '', false].includes(value)
  }

  /**
   * Should return a string containing the error if the value is invalid. If the
   * value is valid, then null must be returned.
   */
  getValidationError(field, value) {
    return null
  }

  /**
   * Indicates whether or not it is possible to sort in a view.
   */
  getCanSortInView(field) {
    return true
  }

  /**
   * Indicates if is possible for the field type to be the primary field.
   */
  getCanBePrimaryField() {
    return true
  }

  constructor(...args) {
    super(...args)
    this.type = this.getType()
    this.iconClass = this.getIconClass()
    this.canBePrimaryField = this.getCanBePrimaryField()
    this.isReadOnly = this.getIsReadOnly()

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
      name: this.getName(),
      isReadOnly: this.isReadOnly,
      canImport: this.getCanImport(),
    }
  }

  /**
   * Should return a for humans readable representation of the value. This is for
   * example used by the link row field and row modal. This is not a problem with most
   * fields like text or number, but some store a more complex object like
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
    // In case that the 'value' is null or undefined (which means that the cell is empty)
    // we simply want to return an empty string.
    if (value == null) {
      return ''
    } else {
      return value.toString()
    }
  }

  /**
   * Some fields need two representations: a simple textual one returned by
   * `.prepareValueForCopy()` but also a rich representation in json to avoid data
   * loss while copying. For example: a select field can have multiple options with the
   * same name. If we copy just text, we'll loose which option it was before if there
   * are duplicate name but with the rich version we can restore the exact same data.
   * The value returned by this method is then copied in a specific clipboard buffer to
   * avoid messing up with the text buffer. The returned value must be json
   * serializable.
   * This method don't have to be redefined and return `prepareValueForCopy()` value
   * by default.
   */
  prepareRichValueForCopy(field, value) {
    return this.prepareValueForCopy(field, value)
  }

  /**
   * This hook is called before the field's value is overwritten by the clipboard
   * data. That data might needs to be prepared so that the field accepts it.
   * By default the input value is returned as is. You can also use the
   * `richClipboardData` parameter to restore a field without data loss. Using this
   * parameter only makes sense if you've also defined a specific
   * `.prepareRichValueForCopy()` method that return this rich value.
   */
  prepareValueForPaste(field, clipboardData, richClipboardData) {
    return clipboardData
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
  getDocsFieldResponseExample(
    { id, table_id: tableId, name, order, type, primary },
    readOnly
  ) {
    return {
      id,
      table_id: tableId,
      name,
      order,
      type,
      primary,
      read_only: readOnly,
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
      this.getContainsFilterFunction(field)(
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
      !this.getContainsFilterFunction(field)(
        rowValue,
        this.toHumanReadableString(field, rowValue),
        filterValue
      )
    )
  }

  /**
   * Is called for each field in the row when another field value in the row has
   * changed. Optionally, a different value can be returned here for that field. This
   * is for example used by the last modified field type to update the last modified
   * value in real time when a row has changed.
   */
  onRowChange(row, currentField, currentFieldValue) {
    return currentFieldValue
  }

  /**
   * Is called for each field in the row when a row has moved to another position.
   * Optionally, a different value can be returned here for that field. This is for
   * example used by the last modified field type to update the last modified value
   * in real time when a row has moved.
   */
  onRowMove(row, order, oldOrder, currentField, currentFieldValue) {
    return currentFieldValue
  }

  /**
   * Is called for each field in a row when a new row is being created. This can be
   * used to set a default value. This value will be added to the row before the
   * call submitted to the backend, so the user will immediately see it.
   */
  getNewRowValue(field) {
    return this.getEmptyValue(field)
  }

  /**
   * Determines whether row data of the field should be fetched again after the
   * field has been created. This is for example needed when a value depends on the
   * backend and can't be guessed or calculated by the web-frontend.
   */
  shouldFetchDataWhenAdded() {
    return false
  }

  /**
   * Determines whether the fieldType is a read only field. Read only fields will be
   * excluded from update requests to the backend. It is also not possible to change
   * the value by for example pasting.
   */
  getIsReadOnly() {
    return false
  }

  /**
   * Override and return true if the field type can be referenced by a formula field.
   * @return {boolean}
   */
  canBeReferencedByFormulaField() {
    return false
  }

  /**
   * Determines whether a field type should automatically fetch select options
   * when switching to a field type that supports select options, like the single or
   * multiple select.
   */
  shouldFetchFieldSelectOptions() {
    return true
  }

  /**
   * Indicates whether this field type accepts single select suggestions splitted by
   * a comma.  This is for example the case with a multiple select field because
   * splits old values by comma on conversion.
   */
  acceptSplitCommaSeparatedSelectOptions() {
    return false
  }

  /**
   * Determines whether the field type value can be set by
   * parsing a query parameter.
   * @returns {boolean}
   */
  canParseQueryParameter() {
    return false
  }

  /**
   * Parse a value given by a url query parameter.
   * @param {string} value
   * @param field
   * @param options Any additional information that might be needed for the parsing
   * @returns {*}
   */
  parseQueryParameter(field, value, options) {
    return value
  }

  /**
   * Determines whether the field type value can be imported from a file
   * @returns {boolean}
   */
  getCanImport() {
    return false
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
    const { i18n } = this.app
    return i18n.t('fieldType.singleLineText')
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

  getCardComponent() {
    return RowCardFieldText
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
    return this.app.i18n.t('fieldDocs.text')
  }

  getDocsRequestExample(field) {
    return 'string'
  }

  getContainsFilterFunction() {
    return genericContainsFilter
  }

  canBeReferencedByFormulaField() {
    return true
  }

  canParseQueryParameter() {
    return true
  }

  getCanImport() {
    return true
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
    const { i18n } = this.app
    return i18n.t('fieldType.longText')
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

  getCardComponent() {
    return RowCardFieldText
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
    return this.app.i18n.t('fieldDocs.longText')
  }

  getDocsRequestExample(field) {
    return 'string'
  }

  getContainsFilterFunction() {
    return genericContainsFilter
  }

  canBeReferencedByFormulaField() {
    return true
  }

  canParseQueryParameter() {
    return true
  }

  getCanImport() {
    return true
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
    const { i18n } = this.app
    return i18n.t('fieldType.linkToTable')
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

  getFormViewFieldComponent() {
    return FormViewFieldLinkRow
  }

  getCardComponent() {
    return RowCardFieldLinkRow
  }

  getEmptyValue(field) {
    return []
  }

  getCanSortInView(field) {
    return false
  }

  getCanBePrimaryField() {
    return false
  }

  /**
   * The structure for updating is slightly different than what we need for displaying
   * the value because the display value does not have to be included. Here we convert
   * the array[object] structure to an array[id] structure.
   */
  prepareValueForUpdate(field, value) {
    return value.map((item) => {
      if (typeof item === 'object') {
        return item.id === null ? item.value : item.id
      } else {
        return item
      }
    })
  }

  prepareValueForCopy(field, value) {
    if (!Array.isArray(value)) {
      return ''
    }

    const nameList = value.map(({ value }) => value)
    // Use papa to generate a CSV string
    return this.app.$papa.arrayToString(nameList)
  }

  prepareRichValueForCopy(field, value) {
    return {
      tableId: field.link_row_table_id,
      value,
    }
  }

  checkRichValueIsCompatible(value) {
    return (
      value === null ||
      (typeof value === 'object' &&
        Object.prototype.hasOwnProperty.call(value, 'tableId') &&
        Object.prototype.hasOwnProperty.call(value, 'value') &&
        value.value.every(
          (row) =>
            Object.prototype.hasOwnProperty.call(row, 'id') &&
            Object.prototype.hasOwnProperty.call(row, 'value')
        ))
    )
  }

  prepareValueForPaste(field, clipboardData, richClipboardData) {
    if (
      this.checkRichValueIsCompatible(richClipboardData) &&
      field.link_row_table_id === richClipboardData.tableId
    ) {
      if (richClipboardData === null) {
        return []
      }
      return richClipboardData.value
    } else {
      // No fallback to text for now
      return []
    }
  }

  toHumanReadableString(field, value) {
    if (value) {
      return value.map((link) => link.value).join(', ')
    }
    return ''
  }

  /**
   * When a table is deleted it might be the case that this is the related table of
   * the field. If so it means that this field has already been deleted and it needs
   * to be removed from the store without making an API call.
   */
  tableDeleted({ dispatch }, field, table, database) {
    if (field.link_row_table_id === table.id) {
      dispatch('field/forceDelete', field, { root: true })
    }
  }

  getDocsDataType(field) {
    return 'array'
  }

  getDocsDescription(field) {
    return this.app.i18n.t('fieldDocs.linkRow', {
      table: field.link_row_table_id,
    })
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

  canBeReferencedByFormulaField() {
    return true
  }

  shouldFetchFieldSelectOptions() {
    return false
  }

  canParseQueryParameter() {
    return true
  }

  async parseQueryParameter(field, value, { client, slug, publicAuthToken }) {
    const { data } = await ViewService(client).linkRowFieldLookup(
      slug,
      field.field.id,
      1,
      value,
      1,
      publicAuthToken
    )

    const item = data.results.find((item) => item.value === value)

    return item ? [item] : this.getEmptyValue()
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
    const { i18n } = this.app
    return i18n.t('fieldType.number')
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

  getCardComponent() {
    return RowCardFieldNumber
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

  getValidationError(field, value) {
    if (value === null || value === '') {
      return null
    }

    // Transform any commas to dots
    const valueWithDots =
      typeof value === 'string'
        ? NumberFieldType.unlocalizeString(value)
        : value

    if (isNaN(parseFloat(valueWithDots)) || !isFinite(valueWithDots)) {
      return this.app.i18n.t('fieldErrors.invalidNumber')
    }
    if (
      valueWithDots.split('.')[0].replace('-', '').length >
      NumberFieldType.getMaxNumberLength()
    ) {
      return this.app.i18n.t('fieldErrors.maxDigits', {
        max: NumberFieldType.getMaxNumberLength(),
      })
    }
    return null
  }

  /**
   * First checks if the value is numeric, if that is the case, the number is going
   * to be formatted.
   */
  prepareValueForPaste(field, clipboardData) {
    const value = clipboardData
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
   * if too much decimal places are provided and if negative numbers aren't allowed
   * they will be set to 0.
   */
  static formatNumber(field, value) {
    const valueWithDots =
      typeof value === 'string'
        ? NumberFieldType.unlocalizeString(value)
        : value

    if (
      valueWithDots === '' ||
      isNaN(valueWithDots) ||
      valueWithDots === undefined ||
      valueWithDots === null
    ) {
      return null
    }
    let number = new BigNumber(valueWithDots)
    if (!field.number_negative && number.isLessThan(0)) {
      number = 0
    }
    return number.toFixed(field.number_decimal_places)
  }

  static unlocalizeString(value) {
    return value.replace(/,/g, '.')
  }

  getDocsDataType(field) {
    return field.number_decimal_places > 0 ? 'decimal' : 'number'
  }

  getDocsDescription(field) {
    let t = field.number_decimal_places === 0 ? 'number' : 'decimal'
    if (!field.number_negative) {
      t += 'Positive'
    }
    return this.app.i18n.t(`fieldDocs.${t}`, {
      places: field.number_decimal_places,
    })
  }

  getDocsRequestExample(field) {
    if (field.number_decimal_places > 0) {
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

  canBeReferencedByFormulaField() {
    return true
  }

  canParseQueryParameter() {
    return true
  }

  parseQueryParameter(field, value) {
    return NumberFieldType.formatNumber(field.field, value)
  }

  getCanImport() {
    return true
  }
}

export class RatingFieldType extends FieldType {
  static getMaxNumberLength() {
    return 2
  }

  static getType() {
    return 'rating'
  }

  getIconClass() {
    return 'star'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('fieldType.rating')
  }

  getFormComponent() {
    return FieldRatingSubForm
  }

  getGridViewFieldComponent() {
    return GridViewFieldRating
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldRating
  }

  getRowEditFieldComponent() {
    return RowEditFieldRating
  }

  getCardComponent() {
    return RowCardFieldRating
  }

  getSortIndicator() {
    return ['text', '1', '9']
  }

  getEmptyValue(field) {
    return 0
  }

  getSort(name, order) {
    return (a, b) => {
      if (a[name] === b[name]) {
        return 0
      }

      const numberA = a[name]
      const numberB = b[name]

      return order === 'ASC'
        ? numberA < numberB
          ? -1
          : 1
        : numberB < numberA
        ? -1
        : 1
    }
  }

  /**
   * First checks if the value is numeric, if that is the case, the number is going
   * to be formatted.
   */
  prepareValueForPaste(field, clipboardData) {
    const pastedValue = clipboardData
    const value = parseInt(pastedValue, 10)

    if (isNaN(value) || !isFinite(value)) {
      return 0
    }

    // Clamp the value
    if (value < 0) {
      return 0
    }
    if (value > field.max_value) {
      return field.max_value
    }
    return value
  }

  getDocsDataType(field) {
    return 'number'
  }

  getDocsDescription(field) {
    return this.app.i18n.t(`fieldDocs.rating`)
  }

  getDocsRequestExample(field) {
    return 3
  }

  getContainsFilterFunction() {
    return genericContainsFilter
  }

  canBeReferencedByFormulaField() {
    return true
  }

  canParseQueryParameter() {
    return true
  }

  parseQueryParameter(field, value) {
    const valueParsed = parseInt(value, 10)

    if (isNaN(valueParsed) || valueParsed < 0) {
      return this.getEmptyValue()
    }

    if (valueParsed > field.max_value) {
      return field.max_value
    }

    return valueParsed
  }

  getCanImport() {
    return true
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
    const { i18n } = this.app
    return i18n.t('fieldType.boolean')
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

  getCardComponent() {
    return RowCardFieldBoolean
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
    if (!clipboardData) {
      clipboardData = ''
    }
    const value = clipboardData.toLowerCase().trim()
    return trueString.includes(value)
  }

  getDocsDataType(field) {
    return 'boolean'
  }

  getDocsDescription(field) {
    return this.app.i18n.t('fieldDocs.boolean')
  }

  getDocsRequestExample(field) {
    return true
  }

  canBeReferencedByFormulaField() {
    return true
  }

  canParseQueryParameter() {
    return true
  }

  parseQueryParameter(field, value) {
    return value === 'true'
  }

  getCanImport() {
    return true
  }
}

class BaseDateFieldType extends FieldType {
  getIconClass() {
    return 'calendar-alt'
  }

  getSortIndicator() {
    return ['text', '1', '9']
  }

  getFormComponent() {
    return FieldDateSubForm
  }

  getCardComponent() {
    return RowCardFieldDate
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
    const date = moment.tz(value, field.timezone)

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

  prepareValueForCopy(field, value) {
    return this.toHumanReadableString(field, value)
  }

  prepareRichValueForCopy(field, value) {
    return value
  }

  /**
   * Tries to parse the clipboard text value with moment and returns the date in the
   * correct format for the field. If it can't be parsed null is returned.
   */
  prepareValueForPaste(field, clipboardData) {
    if (!clipboardData) {
      clipboardData = ''
    }
    return DateFieldType.formatDate(field, clipboardData)
  }

  static formatDate(field, dateString) {
    const value = dateString.toUpperCase()

    // Formats for ISO dates
    let formats = [
      moment.ISO_8601,
      'YYYY-MM-DD',
      'YYYY-MM-DD hh:mm A',
      'YYYY-MM-DD HH:mm',
    ]
    // Formats for EU dates
    const EUFormat = ['DD/MM/YYYY', 'DD/MM/YYYY hh:mm A', 'DD/MM/YYYY HH:mm']
    // Formats for US dates
    const USFormat = ['MM/DD/YYYY', 'MM/DD/YYYY hh:mm A', 'MM/DD/YYYY HH:mm']

    // Interpret the pasted date based on the field's current date format
    if (field.date_format === 'EU') {
      formats = formats.concat(EUFormat).concat(USFormat)
    } else if (field.date_format === 'US') {
      formats = formats.concat(USFormat).concat(EUFormat)
    }

    const date = moment.utc(value, formats)

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
      ? this.app.i18n.t('fieldDocs.dateTime')
      : this.app.i18n.t('fieldDocs.date')
  }

  getDocsRequestExample(field) {
    return field.date_include_time ? '2020-01-01T12:00:00Z' : '2020-01-01'
  }

  getContainsFilterFunction() {
    return genericContainsFilter
  }

  canBeReferencedByFormulaField() {
    return true
  }

  getCanImport() {
    return true
  }
}

export class DateFieldType extends BaseDateFieldType {
  static getType() {
    return 'date'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('fieldType.date')
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

  canParseQueryParameter() {
    return true
  }

  parseQueryParameter(field, value) {
    return DateFieldType.formatDate(field.field, value)
  }
}

export class CreatedOnLastModifiedBaseFieldType extends BaseDateFieldType {
  getIsReadOnly() {
    return true
  }

  getFormComponent() {
    return FieldCreatedOnLastModifiedSubForm
  }

  getFormViewFieldComponent() {
    return null
  }

  getRowEditFieldComponent() {
    return RowEditFieldDateReadOnly
  }

  getGridViewFieldComponent() {
    return GridViewFieldDateReadOnly
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldDate
  }

  /**
   * The "new row" value for the new row in the case of LastModified or CreatedOn Fields
   * is simply the current time.
   */
  getNewRowValue() {
    return moment().utc().format()
  }

  shouldFetchDataWhenAdded() {
    return true
  }

  getDocsDataType(field) {
    return null
  }

  getDocsDescription(field, firstPartOverwrite) {
    const firstPart =
      firstPartOverwrite || this.app.i18n.t('fieldDocs.readOnly')
    return field.date_include_time
      ? `${firstPart} ${this.app.i18n.t('fieldDocs.dateTimeResponse')}`
      : `${firstPart} ${this.app.i18n.t('fieldDocs.dateResponse')}`
  }

  getDocsRequestExample(field) {
    return field.date_include_time ? '2020-01-01T12:00:00Z' : '2020-01-01'
  }

  getContainsFilterFunction() {
    return genericContainsFilter
  }
}

export class LastModifiedFieldType extends CreatedOnLastModifiedBaseFieldType {
  static getType() {
    return 'last_modified'
  }

  getIconClass() {
    return 'edit'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('fieldType.lastModified')
  }

  getDocsDescription(field) {
    return super.getDocsDescription(
      field,
      this.app.i18n.t('fieldDocs.lastModifiedReadOnly')
    )
  }

  _onRowChangeOrMove() {
    return moment().utc().format()
  }

  onRowChange(row, currentField, currentFieldValue) {
    return this._onRowChangeOrMove()
  }

  onRowMove(row, order, oldOrder, currentField, currentFieldValue) {
    return this._onRowChangeOrMove()
  }
}

export class CreatedOnFieldType extends CreatedOnLastModifiedBaseFieldType {
  static getType() {
    return 'created_on'
  }

  getIconClass() {
    return 'plus'
  }

  getDocsDescription(field) {
    return super.getDocsDescription(
      field,
      this.app.i18n.t('fieldDocs.createdOnReadOnly')
    )
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('fieldType.createdOn')
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
    const { i18n } = this.app
    return i18n.t('fieldType.url')
  }

  getGridViewFieldComponent() {
    return GridViewFieldURL
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldURL
  }

  getRowEditFieldComponent() {
    return RowEditFieldURL
  }

  getCardComponent() {
    return RowCardFieldURL
  }

  prepareValueForPaste(field, clipboardData) {
    const value = clipboardData
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

  getEmptyValue(field) {
    return ''
  }

  getValidationError(field, value) {
    if (value === null || value === '') {
      return null
    }
    if (!isValidURL(value)) {
      return this.app.i18n.t('fieldErrors.invalidUrl')
    }
    return null
  }

  getDocsDataType(field) {
    return 'string'
  }

  getDocsDescription(field) {
    return this.app.i18n.t('fieldDocs.url')
  }

  getDocsRequestExample(field) {
    return 'https://baserow.io'
  }

  getContainsFilterFunction() {
    return genericContainsFilter
  }

  canParseQueryParameter() {
    return true
  }

  canBeReferencedByFormulaField() {
    return true
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
    const { i18n } = this.app
    return i18n.t('fieldType.email')
  }

  getGridViewFieldComponent() {
    return GridViewFieldEmail
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldURL
  }

  getRowEditFieldComponent() {
    return RowEditFieldEmail
  }

  getCardComponent() {
    return RowCardFieldEmail
  }

  prepareValueForPaste(field, clipboardData) {
    const value = clipboardData
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

  getEmptyValue(field) {
    return ''
  }

  getValidationError(field, value) {
    if (value === null || value === '') {
      return null
    }
    if (value.length > 254) {
      return this.app.i18n.t('fieldErrors.max254Chars')
    }
    if (!isValidEmail(value)) {
      return this.app.i18n.t('fieldErrors.invalidEmail')
    }
    return null
  }

  getDocsDataType(field) {
    return 'string'
  }

  getDocsDescription(field) {
    return this.app.i18n.t('fieldDocs.email')
  }

  getDocsRequestExample(field) {
    return 'example@baserow.io'
  }

  getContainsFilterFunction() {
    return genericContainsFilter
  }

  canBeReferencedByFormulaField() {
    return true
  }

  canParseQueryParameter() {
    return true
  }

  getCanImport() {
    return true
  }
}

export class FileFieldType extends FieldType {
  fileRegex = /^(.+\.[^\s]+) \(http[^)]+\/([^\s]+.[^\s]+)\)$/
  fileURLRegex = /^http[^)]+\/([^\s]+.[^\s]+)$/

  static getType() {
    return 'file'
  }

  getIconClass() {
    return 'file'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('fieldType.file')
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

  getFormViewFieldComponentProperties({ $store, $client, slug }) {
    const userFileUploadTypes = [UploadFileUserFileUploadType.getType()]
    return {
      userFileUploadTypes,
      uploadFile: (file, progress) => {
        return FormService($client).uploadFile(
          file,
          progress,
          slug,
          $store.getters['page/view/public/getAuthToken']
        )
      },
    }
  }

  getCardComponent() {
    return RowCardFieldFile
  }

  toHumanReadableString(field, value) {
    return value.map((file) => file.visible_name).join(', ')
  }

  prepareValueForCopy(field, value) {
    if (value === undefined || value === null) {
      return ''
    }

    return this.app.$papa.arrayToString(
      value.map(
        ({ url, visible_name: visibleName }) => `${visibleName} (${url})`
      )
    )
  }

  prepareRichValueForCopy(field, value) {
    return value
  }

  checkRichValueIsCompatible(values) {
    return (
      Array.isArray(values) &&
      values.every(
        (value) =>
          Object.prototype.hasOwnProperty.call(value, 'name') ||
          Object.prototype.hasOwnProperty.call(value, 'url')
      )
    )
  }

  prepareValueForPaste(field, clipboardData, richClipboardData) {
    if (this.checkRichValueIsCompatible(richClipboardData)) {
      return richClipboardData
        .map((file) => {
          if (Object.prototype.hasOwnProperty.call(file, 'name')) {
            return file
          } else if (isValidURL(file.url)) {
            const name = getFilenameFromUrl(file.url)
            return { ...file, name }
          } else {
            return null
          }
        })
        .filter((f) => f)
    } else {
      try {
        const files = this.app.$papa.stringToArray(clipboardData)
        return files
          .map((strValue) => {
            // Try to match the expected format
            const matches = strValue.match(this.fileRegex)
            if (matches) {
              return {
                name: matches[2],
                visible_name: matches[1],
              }
            } else {
              return null
            }
          })
          .filter((v) => v)
      } catch {
        return []
      }
    }
  }

  getEmptyValue(field) {
    return []
  }

  getCanSortInView(field) {
    return false
  }

  getDocsDataType() {
    return 'array'
  }

  getDocsDescription() {
    return this.app.i18n.t('fieldDocs.file')
  }

  getDocsRequestExample() {
    return [
      {
        name: 'VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png',
      },
    ]
  }

  getDocsResponseExample() {
    return [
      {
        url: 'https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png',
        thumbnails: {
          tiny: {
            url: 'https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png',
            width: 21,
            height: 21,
          },
          small: {
            url: 'https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png',
            width: 48,
            height: 48,
          },
        },
        name: 'VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png',
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

  shouldFetchFieldSelectOptions() {
    return false
  }

  getCanImport() {
    return true
  }
}

export class SingleSelectFieldType extends FieldType {
  static getType() {
    return 'single_select'
  }

  getIconClass() {
    return 'chevron-circle-down'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('fieldType.singleSelect')
  }

  getFormComponent() {
    return FieldSelectOptionsSubForm
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

  getFormViewFieldComponentProperties() {
    return {
      'allow-create-options': false,
    }
  }

  getCardComponent() {
    return RowCardFieldSingleSelect
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
    return value.value
  }

  prepareRichValueForCopy(field, value) {
    if (value === undefined) {
      return null
    }
    return value
  }

  _findOptionWithMatchingId(field, rawTextValue) {
    if (isNumeric(rawTextValue)) {
      const pastedOptionId = parseInt(rawTextValue, 10)
      return field.select_options.find((option) => option.id === pastedOptionId)
    }
    return undefined
  }

  _findOptionWithMatchingValue(field, rawTextValue) {
    const trimmedPastedText = rawTextValue.trim()
    return field.select_options.find(
      (option) => option.value === trimmedPastedText
    )
  }

  checkRichValueIsCompatible(value) {
    return (
      value === null ||
      (typeof value === 'object' &&
        Object.prototype.hasOwnProperty.call(value, 'id'))
    )
  }

  prepareValueForPaste(field, clipboardData, richClipboardData) {
    if (this.checkRichValueIsCompatible(richClipboardData)) {
      if (richClipboardData === null) {
        return null
      }
      return this._findOptionWithMatchingId(field, richClipboardData.id)
    } else {
      if (!clipboardData) {
        return null
      }
      return (
        this._findOptionWithMatchingId(field, clipboardData) ||
        this._findOptionWithMatchingValue(field, clipboardData)
      )
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
      ${this.app.i18n.t('fieldDocs.singleSelect')}
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

  canBeReferencedByFormulaField() {
    return true
  }

  shouldFetchFieldSelectOptions() {
    return false
  }

  canParseQueryParameter() {
    return true
  }

  parseQueryParameter(field, value) {
    const selectedOption = field.field.select_options.find(
      (option) => option.value === value
    )

    return selectedOption ?? this.getEmptyValue()
  }

  getCanImport() {
    return true
  }
}

export class MultipleSelectFieldType extends FieldType {
  static getType() {
    return 'multiple_select'
  }

  getIconClass() {
    return 'list'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('fieldType.multipleSelect')
  }

  getFormComponent() {
    return FieldSelectOptionsSubForm
  }

  getGridViewFieldComponent() {
    return GridViewFieldMultipleSelect
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldMultipleSelect
  }

  getRowEditFieldComponent() {
    return RowEditFieldMultipleSelect
  }

  getFormViewFieldComponentProperties() {
    return {
      'allow-create-options': false,
    }
  }

  getCardComponent() {
    return RowCardFieldMultipleSelect
  }

  getSort(name, order) {
    return (a, b) => {
      const valuesA = a[name]
      const valuesB = b[name]
      const stringA =
        valuesA.length > 0 ? valuesA.map((obj) => obj.value).join('') : ''
      const stringB =
        valuesB.length > 0 ? valuesB.map((obj) => obj.value).join('') : ''

      return order === 'ASC'
        ? stringA.localeCompare(stringB)
        : stringB.localeCompare(stringA)
    }
  }

  prepareValueForUpdate(field, value) {
    if (value === undefined || value === null) {
      return []
    }
    return value.map((item) => item.id)
  }

  prepareValueForCopy(field, value) {
    if (value === undefined || value === null) {
      return ''
    }

    const nameList = value.map(({ value }) => value)
    // Use papa to generate a CSV string
    return this.app.$papa.arrayToString(nameList)
  }

  prepareRichValueForCopy(field, value) {
    if (value === undefined) {
      return []
    }
    return value
  }

  checkRichValueIsCompatible(value) {
    return (
      value === null ||
      (Array.isArray(value) &&
        value.every((v) => Object.prototype.hasOwnProperty.call(v, 'id')))
    )
  }

  prepareValueForPaste(field, clipboardData, richClipboardData) {
    if (this.checkRichValueIsCompatible(richClipboardData)) {
      if (richClipboardData === null) {
        return []
      }

      return richClipboardData
    } else {
      // Fallback to text version
      try {
        const data = this.app.$papa.stringToArray(clipboardData)

        const selectOptionMap = Object.fromEntries(
          field.select_options.map((option) => [option.value, option])
        )

        const uniqueValuesOnly = Array.from(new Set(data))

        return uniqueValuesOnly
          .filter((name) => Object.keys(selectOptionMap).includes(name))
          .map((name) => selectOptionMap[name])
      } catch (e) {
        return []
      }
    }
  }

  toHumanReadableString(field, value) {
    if (value === undefined || value === null || value === []) {
      return ''
    }
    return value.map((item) => item.value).join(', ')
  }

  getDocsDataType() {
    return 'array'
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
      ${this.app.i18n.t('fieldDocs.multipleSelect')}
      <br />
      ${options}
    `
  }

  getDocsRequestExample() {
    return [1]
  }

  getDocsResponseExample() {
    return [
      {
        id: 1,
        value: 'Option',
        color: 'light-blue',
      },
    ]
  }

  getContainsFilterFunction() {
    return genericContainsFilter
  }

  getEmptyValue() {
    return []
  }

  shouldFetchFieldSelectOptions() {
    return false
  }

  acceptSplitCommaSeparatedSelectOptions() {
    return true
  }

  canParseQueryParameter() {
    return true
  }

  /**
   * Accepts the following format: option1,option2,option3
   */
  parseQueryParameter(field, value) {
    const values = value.split(',')

    const selectOptions = field.field.select_options.filter((option) =>
      values.includes(option.value)
    )

    return selectOptions.length > 0 ? selectOptions : this.getEmptyValue()
  }

  getCanImport() {
    return true
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
    const { i18n } = this.app
    return i18n.t('fieldType.phoneNumber')
  }

  getGridViewFieldComponent() {
    return GridViewFieldPhoneNumber
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldURL
  }

  getRowEditFieldComponent() {
    return RowEditFieldPhoneNumber
  }

  getCardComponent() {
    return RowCardFieldPhoneNumber
  }

  prepareValueForPaste(field, clipboardData) {
    const value = clipboardData
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

  getEmptyValue(field) {
    return ''
  }

  getValidationError(field, value) {
    if (value === null || value === '') {
      return null
    }
    if (!isSimplePhoneNumber(value)) {
      return this.app.i18n.t('fieldErrors.invalidPhoneNumber')
    }
    return null
  }

  getSortIndicator() {
    return ['text', '0', '9']
  }

  getDocsDataType(field) {
    return 'string'
  }

  getDocsDescription(field) {
    return this.app.i18n.t('fieldDocs.phoneNumber')
  }

  getDocsRequestExample(field) {
    return '+1-541-754-3010'
  }

  getContainsFilterFunction() {
    return genericContainsFilter
  }

  canBeReferencedByFormulaField() {
    return true
  }

  canParseQueryParameter() {
    return true
  }

  parseQueryParameter(field, value) {
    return value
  }

  getCanImport() {
    return true
  }
}

export class FormulaFieldType extends FieldType {
  static getType() {
    return 'formula'
  }

  static compatibleWithFormulaTypes(...formulaTypeStrings) {
    return (field) => {
      return (
        field.type === this.getType() &&
        formulaTypeStrings.includes(field.formula_type)
      )
    }
  }

  getIconClass() {
    return 'square-root-alt'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('fieldType.formula')
  }

  getGridViewFieldComponent() {
    return GridViewFieldFormula
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldFormula
  }

  getRowEditFieldComponent() {
    return RowEditFieldFormula
  }

  getCardComponent() {
    return RowCardFieldFormula
  }

  _mapFormulaTypeToFieldType(formulaType) {
    return this.app.$registry.get('formula_type', formulaType).getFieldType()
  }

  getCardValueHeight(field) {
    return (
      this.app.$registry
        .get('formula_type', field.formula_type)
        .getCardComponent().height || 0
    )
  }

  getSort(name, order, field) {
    const underlyingFieldType = this.app.$registry.get(
      'field',
      this._mapFormulaTypeToFieldType(field.formula_type)
    )
    return underlyingFieldType.getSort(name, order)
  }

  getEmptyValue(field) {
    return null
  }

  getDocsDataType(field) {
    return this.app.$registry
      .get('formula_type', field.formula_type)
      .getDocsDataType(field)
  }

  getDocsDescription(field) {
    return this.app.i18n.t('fieldDocs.formula')
  }

  getDocsRequestExample(field) {
    return 'it is invalid to include request data for this field as it is read only'
  }

  getDocsResponseExample(field) {
    return this.app.$registry
      .get('formula_type', field.formula_type)
      .getDocsResponseExample(field)
  }

  prepareValueForCopy(field, value) {
    const subType = this.app.$registry.get('formula_type', field.formula_type)
    return subType.prepareValueForCopy(field, value)
  }

  getContainsFilterFunction(field) {
    const underlyingFieldType = this.app.$registry.get(
      'field',
      this._mapFormulaTypeToFieldType(field.formula_type)
    )
    return underlyingFieldType.getContainsFilterFunction()
  }

  toHumanReadableString(field, value) {
    return this.app.$registry
      .get('formula_type', field.formula_type)
      .toHumanReadableString(field, value)
  }

  getSortIndicator(field) {
    const underlyingFieldType = this.app.$registry.get(
      'field',
      this._mapFormulaTypeToFieldType(field.formula_type)
    )
    return underlyingFieldType.getSortIndicator()
  }

  getFormComponent() {
    return FieldFormulaSubForm
  }

  getIsReadOnly() {
    return true
  }

  shouldFetchDataWhenAdded() {
    return true
  }

  getFormViewFieldComponent() {
    return null
  }

  canBeReferencedByFormulaField() {
    return true
  }

  getCanSortInView(field) {
    const subType = this.app.$registry.get('formula_type', field.formula_type)
    return subType.getCanSortInView()
  }
}

export class LookupFieldType extends FormulaFieldType {
  static getType() {
    return 'lookup'
  }

  getIconClass() {
    return 'binoculars'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('fieldType.lookup')
  }

  getDocsDescription(field) {
    return this.app.i18n.t('fieldDocs.lookup')
  }

  getFormComponent() {
    return FieldLookupSubForm
  }

  shouldFetchFieldSelectOptions() {
    return false
  }
}

export class MultipleCollaboratorsFieldType extends FieldType {
  static getType() {
    return 'multiple_collaborators'
  }

  getIconClass() {
    return 'user-friends'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('fieldType.multipleCollaborators')
  }

  getFormComponent() {
    return null
  }

  getGridViewFieldComponent() {
    return GridViewFieldMultipleCollaborators
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldMultipleCollaborators
  }

  getRowEditFieldComponent() {
    return RowEditFieldMultipleCollaborators
  }

  getCardComponent() {
    return RowCardFieldMultipleCollaborators
  }

  prepareValueForUpdate(field, value) {
    if (value === undefined || value === null) {
      return []
    }
    return value
  }

  getFormViewFieldComponent() {
    return null
  }

  getEmptyValue() {
    return []
  }

  getCanImport() {
    return true
  }

  getSort(name, order) {
    return (a, b) => {
      const valuesA = a[name]
      const valuesB = b[name]

      let stringA = ''
      let stringB = ''

      const groups = this.app.store.getters['group/getAll']

      if (valuesA.length > 0 && groups.length > 0) {
        stringA = valuesA
          .map(
            (obj) => this.app.store.getters['group/getUserById'](obj.id).name
          )
          .join('')
      } else if (valuesA.length > 0) {
        stringA = valuesA.map((obj) => obj.name).join('')
      }

      if (valuesB.length > 0 && groups.length > 0) {
        stringB = valuesB
          .map(
            (obj) => this.app.store.getters['group/getUserById'](obj.id).name
          )
          .join('')
      } else if (valuesB.length > 0) {
        stringB = valuesB.map((obj) => obj.name).join('')
      }

      return order === 'ASC'
        ? stringA.localeCompare(stringB)
        : stringB.localeCompare(stringA)
    }
  }

  prepareValueForCopy(field, value) {
    if (value === undefined || value === null) {
      return ''
    }

    const groups = this.app.store.getters['group/getAll']

    let nameList = []

    if (groups.length > 0) {
      nameList = value.map((value) => {
        const groupUser = this.app.store.getters['group/getUserById'](value.id)
        return groupUser.name
      })
    } else {
      // public views
      nameList = value.map((value) => {
        return value.name
      })
    }

    return this.app.$papa.arrayToString(nameList)
  }

  prepareRichValueForCopy(field, value) {
    if (value === undefined) {
      return []
    }
    return value
  }

  checkRichValueIsCompatible(value) {
    return (
      value === null ||
      (Array.isArray(value) &&
        value.every((v) => Object.prototype.hasOwnProperty.call(v, 'id')))
    )
  }

  prepareValueForPaste(field, clipboardData, richClipboardData) {
    if (this.checkRichValueIsCompatible(richClipboardData)) {
      if (richClipboardData === null) {
        return []
      }
      return richClipboardData
    } else {
      // Fallback to text version
      try {
        const data = this.app.$papa.stringToArray(clipboardData)
        const uniqueValuesOnly = Array.from(new Set(data))

        return uniqueValuesOnly
          .map((emailOrName) => {
            const groupUser =
              this.app.store.getters['group/getUserByEmail'](emailOrName)
            if (groupUser !== undefined) {
              return groupUser
            }
            return this.app.store.getters['group/getUserByName'](emailOrName)
          })
          .filter((obj) => obj !== null)
          .map((obj) => {
            return {
              id: obj.user_id,
              name: obj.name,
            }
          })
      } catch (e) {
        return []
      }
    }
  }

  getDocsDataType() {
    return 'array'
  }

  getDocsDescription(field) {
    return this.app.i18n.t('fieldDocs.multipleCollaborators')
  }

  getDocsRequestExample() {
    return [{ id: 1 }]
  }

  getDocsResponseExample() {
    return [
      {
        id: 1,
        name: 'John',
      },
    ]
  }
}
