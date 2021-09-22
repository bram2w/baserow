import moment from '@baserow/modules/core/moment'
import { Registerable } from '@baserow/modules/core/registry'
import ViewFilterTypeText from '@baserow/modules/database/components/view/ViewFilterTypeText'
import ViewFilterTypeNumber from '@baserow/modules/database/components/view/ViewFilterTypeNumber'
import ViewFilterTypeSelectOptions from '@baserow/modules/database/components/view/ViewFilterTypeSelectOptions'
import ViewFilterTypeBoolean from '@baserow/modules/database/components/view/ViewFilterTypeBoolean'
import ViewFilterTypeDate from '@baserow/modules/database/components/view/ViewFilterTypeDate'
import ViewFilterTypeTimeZone from '@baserow/modules/database/components/view/ViewFilterTypeTimeZone'
import ViewFilterTypeLinkRow from '@baserow/modules/database/components/view/ViewFilterTypeLinkRow'
import { trueString } from '@baserow/modules/database/utils/constants'
import { isNumeric } from '@baserow/modules/core/utils/string'
import ViewFilterTypeFileTypeDropdown from '@baserow/modules/database/components/view/ViewFilterTypeFileTypeDropdown'

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

  constructor(...args) {
    super(...args)
    this.type = this.getType()
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
      name: this.getName(),
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
   * Should return the default value when a new filter of this type is created. In
   * almost all cases this should be an empty string, but with timezone sensitive
   * filters we might want use the current timezone.
   */
  getDefaultValue() {
    return ''
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
    const { i18n } = this.app
    return i18n.t('viewFilter.is')
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
    const { i18n } = this.app
    return i18n.t('viewFilter.isNot')
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
    const { i18n } = this.app
    return i18n.t('viewFilter.filenameContains')
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

export class HasFileTypeViewFilterType extends ViewFilterType {
  static getType() {
    return 'has_file_type'
  }

  getName() {
    return 'has file type'
  }

  getExample() {
    return 'image | document'
  }

  getInputComponent() {
    return ViewFilterTypeFileTypeDropdown
  }

  getCompatibleFieldTypes() {
    return ['file']
  }

  matches(rowValue, filterValue, field, fieldType) {
    const isImage = filterValue === 'image'
    const isDocument = filterValue === 'document'

    if (!isImage && !isDocument) {
      return true
    }

    for (let i = 0; i < rowValue.length; i++) {
      if (rowValue[i].is_image === isImage) {
        return true
      }
    }

    return false
  }
}

export class ContainsViewFilterType extends ViewFilterType {
  static getType() {
    return 'contains'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.contains')
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
      'last_modified',
      'created_on',
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
    const { i18n } = this.app
    return i18n.t('viewFilter.containsNot')
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
      'last_modified',
      'created_on',
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
    const { i18n } = this.app
    return i18n.t('viewFilter.isDate')
  }

  getExample() {
    return '2020-01-01'
  }

  getInputComponent() {
    return ViewFilterTypeDate
  }

  getCompatibleFieldTypes() {
    return ['date', 'last_modified', 'created_on']
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (rowValue === null) {
      rowValue = ''
    }

    if (field.timezone) {
      rowValue = moment.utc(rowValue).tz(field.timezone).format('YYYY-MM-DD')
    } else {
      rowValue = rowValue.toString().toLowerCase().trim()
      rowValue = rowValue.slice(0, 10)
    }

    return filterValue === '' || rowValue === filterValue
  }
}

export class DateBeforeViewFilterType extends ViewFilterType {
  static getType() {
    return 'date_before'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.isBeforeDate')
  }

  getExample() {
    return '2020-01-01'
  }

  getInputComponent() {
    return ViewFilterTypeDate
  }

  getCompatibleFieldTypes() {
    return ['date', 'last_modified', 'created_on']
  }

  matches(rowValue, filterValue, field, fieldType) {
    // parse the provided string values as moment objects in order to make
    // date comparisons
    let rowDate = moment.utc(rowValue)
    const filterDate = moment.utc(filterValue)

    if (field.timezone) {
      rowDate = rowDate.tz(field.timezone)
    }

    // if the filter date is not a valid date we can immediately return
    // true because without a valid date the filter won't be applied
    if (!filterDate.isValid()) {
      return true
    }

    // if the row value is null or the rowDate is not valid we can immediately return
    // false since it does not match the filter and the row won't be in the resultset
    if (rowValue === null || !rowDate.isValid()) {
      return false
    }

    return rowDate.isBefore(filterDate, 'day')
  }
}

export class DateAfterViewFilterType extends ViewFilterType {
  static getType() {
    return 'date_after'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.isAfterDate')
  }

  getExample() {
    return '2020-01-01'
  }

  getInputComponent() {
    return ViewFilterTypeDate
  }

  getCompatibleFieldTypes() {
    return ['date', 'last_modified', 'created_on']
  }

  matches(rowValue, filterValue, field, fieldType) {
    // parse the provided string values as moment objects in order to make
    // date comparisons
    let rowDate = moment.utc(rowValue)
    const filterDate = moment.utc(filterValue)

    if (field.timezone) {
      rowDate = rowDate.tz(field.timezone)
    }

    // if the filter date is not a valid date we can immediately return
    // true because without a valid date the filter won't be applied
    if (!filterDate.isValid()) {
      return true
    }

    // if the row value is null or the rowDate is not valid we can immediately return
    // false since it does not match the filter and the row won't be in the resultset
    if (rowValue === null || !rowDate.isValid()) {
      return false
    }

    return rowDate.isAfter(filterDate, 'day')
  }
}

export class DateNotEqualViewFilterType extends ViewFilterType {
  static getType() {
    return 'date_not_equal'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.isNotDate')
  }

  getExample() {
    return '2020-01-01'
  }

  getInputComponent() {
    return ViewFilterTypeDate
  }

  getCompatibleFieldTypes() {
    return ['date', 'last_modified', 'created_on']
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (rowValue === null) {
      rowValue = ''
    }

    if (field.timezone) {
      rowValue = moment.utc(rowValue).tz(field.timezone).format('YYYY-MM-DD')
    } else {
      rowValue = rowValue.toString().toLowerCase().trim()
      rowValue = rowValue.slice(0, 10)
    }

    return filterValue === '' || rowValue !== filterValue
  }
}

export class DateEqualsTodayViewFilterType extends ViewFilterType {
  static getType() {
    return 'date_equals_today'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.isToday')
  }

  getInputComponent() {
    return ViewFilterTypeTimeZone
  }

  getCompatibleFieldTypes() {
    return ['date', 'last_modified', 'created_on']
  }

  getDefaultValue() {
    return new Intl.DateTimeFormat().resolvedOptions().timeZone
  }

  prepareValue() {
    return this.getDefaultValue()
  }

  getSliceLength() {
    // 10: YYYY-MM-DD, 7: YYYY-MM, 4: YYYY
    return 10
  }

  matches(rowValue, filterValue, field) {
    if (rowValue === null) {
      rowValue = ''
    }

    const sliceLength = this.getSliceLength()
    const format = 'YYYY-MM-DD'.slice(0, sliceLength)
    const today = moment().tz(filterValue).format(format)

    if (field.timezone) {
      rowValue = moment.utc(rowValue).tz(field.timezone).format(format)
    } else {
      rowValue = rowValue.toString().toLowerCase().trim()
      rowValue = rowValue.slice(0, sliceLength)
    }

    return rowValue === today
  }
}

export class DateEqualsCurrentMonthViewFilterType extends DateEqualsTodayViewFilterType {
  static getType() {
    return 'date_equals_month'
  }

  getSliceLength() {
    return 7
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.inThisMonth')
  }
}

export class DateEqualsCurrentYearViewFilterType extends DateEqualsTodayViewFilterType {
  static getType() {
    return 'date_equals_year'
  }

  getSliceLength() {
    return 4
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.inThisYear')
  }
}

export class HigherThanViewFilterType extends ViewFilterType {
  static getType() {
    return 'higher_than'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.higherThan')
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
    const { i18n } = this.app
    return i18n.t('viewFilter.lowerThan')
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
    const { i18n } = this.app
    return i18n.t('viewFilter.is')
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
    const { i18n } = this.app
    return i18n.t('viewFilter.isNot')
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
    const { i18n } = this.app
    return i18n.t('viewFilter.is')
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

export class LinkRowHasFilterType extends ViewFilterType {
  static getType() {
    return 'link_row_has'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.has')
  }

  getExample() {
    return '1'
  }

  getInputComponent() {
    return ViewFilterTypeLinkRow
  }

  getCompatibleFieldTypes() {
    return ['link_row']
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (!isNumeric(filterValue)) {
      return true
    }

    const filterValueId = parseInt(filterValue)
    return rowValue.some((relation) => relation.id === filterValueId)
  }
}

export class LinkRowHasNotFilterType extends ViewFilterType {
  static getType() {
    return 'link_row_has_not'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.hasNot')
  }

  getExample() {
    return '1'
  }

  getInputComponent() {
    return ViewFilterTypeLinkRow
  }

  getCompatibleFieldTypes() {
    return ['link_row']
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (!isNumeric(filterValue)) {
      return true
    }

    const filterValueId = parseInt(filterValue)
    return !rowValue.some((relation) => relation.id === filterValueId)
  }
}

export class EmptyViewFilterType extends ViewFilterType {
  static getType() {
    return 'empty'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.isEmpty')
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
      'last_modified',
      'created_on',
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
      (Array.isArray(rowValue) && rowValue.length === 0) ||
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
    const { i18n } = this.app
    return i18n.t('viewFilter.isNotEmpty')
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
      'last_modified',
      'created_on',
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
      (Array.isArray(rowValue) && rowValue.length === 0) ||
      rowValue === false ||
      rowValue.toString().trim() === ''
    )
  }
}
