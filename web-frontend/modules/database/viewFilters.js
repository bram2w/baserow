import moment from '@baserow/modules/core/moment'
import { Registerable } from '@baserow/modules/core/registry'
import ViewFilterTypeText from '@baserow/modules/database/components/view/ViewFilterTypeText'
import ViewFilterTypeNumber from '@baserow/modules/database/components/view/ViewFilterTypeNumber'
import ViewFilterTypeDuration from '@baserow/modules/database/components/view/ViewFilterTypeDuration'
import ViewFilterTypeRating from '@baserow/modules/database/components/view/ViewFilterTypeRating'
import ViewFilterTypeSelectOptions from '@baserow/modules/database/components/view/ViewFilterTypeSelectOptions'
import ViewFilterTypeBoolean from '@baserow/modules/database/components/view/ViewFilterTypeBoolean'
import ViewFilterTypeDate from '@baserow/modules/database/components/view/ViewFilterTypeDate'
import ViewFilterTypeTimeZone from '@baserow/modules/database/components/view/ViewFilterTypeTimeZone'
import ViewFilterTypeNumberWithTimeZone from '@baserow/modules/database/components/view/ViewFilterTypeNumberWithTimeZone'
import ViewFilterTypeLinkRow from '@baserow/modules/database/components/view/ViewFilterTypeLinkRow'
import { trueValues } from '@baserow/modules/core/utils/constants'
import {
  splitTimezoneAndFilterValue,
  DATE_FILTER_TIMEZONE_VALUE_SEPARATOR,
} from '@baserow/modules/database/utils/date'
import { isNumeric } from '@baserow/modules/core/utils/string'
import ViewFilterTypeFileTypeDropdown from '@baserow/modules/database/components/view/ViewFilterTypeFileTypeDropdown'
import ViewFilterTypeCollaborators from '@baserow/modules/database/components/view/ViewFilterTypeCollaborators'
import {
  FormulaFieldType,
  NumberFieldType,
  RatingFieldType,
  DurationFieldType,
} from '@baserow/modules/database/fieldTypes'

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
   * they want to filter on.
   */
  getInputComponent() {
    return null
  }

  /**
    Informs forms whether the component returned by getInputComponent
    is user configurable, or just displays static data which they can't alter.
   */
  get hasEditableValue() {
    return true
  }

  /**
   * Should return the default value when a new filter of this type is created. In
   * almost all cases this should be an empty string, but with timezone sensitive
   * filters we might want use the current timezone.
   */
  getDefaultValue(field) {
    return ''
  }

  /**
   * Optionally, right before updating the string value can be prepared. This could for
   * example be used to convert the value to a number.
   */
  prepareValue(value, field) {
    return value
  }

  /**
   * Should return the field type names that the filter is compatible with or
   * functions which take a field and return a boolean indicating if the field is
   * compatible or not.
   *
   * So for example ['text', 'long_text']. When that field is selected as filter it
   * is only possible to select compatible filter types.
   *
   * Or using a function you could do [(field) => field.some_prop === 10, 'long_text']
   * and then fields which pass the test defined by the function will be deemed as
   * compatible.
   *
   * If no filters are compatible with a field then that field will be disabled.
   */
  getCompatibleFieldTypes() {
    return []
  }

  /**
   * Determines whether the particular filter type will be available
   * in public views.
   */
  isAllowedInPublicViews() {
    return true
  }

  /**
   * Returns if a given field is compatible with this view filter or not. Uses the
   * list provided by getCompatibleFieldTypes to calculate this.
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

  getInputComponent(field) {
    const inputComponent = {
      [RatingFieldType.getType()]: ViewFilterTypeRating,
      [NumberFieldType.getType()]: ViewFilterTypeNumber,
      [DurationFieldType.getType()]: ViewFilterTypeDuration,
    }
    return inputComponent[field?.type] || ViewFilterTypeText
  }

  getCompatibleFieldTypes() {
    return [
      'text',
      'long_text',
      'url',
      'email',
      'number',
      'rating',
      'phone_number',
      'uuid',
      'autonumber',
      'duration',
      FormulaFieldType.compatibleWithFormulaTypes('text', 'char', 'number'),
    ]
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

  getInputComponent(field) {
    const inputComponent = {
      [RatingFieldType.getType()]: ViewFilterTypeRating,
      [NumberFieldType.getType()]: ViewFilterTypeNumber,
      [DurationFieldType.getType()]: ViewFilterTypeDuration,
    }
    return inputComponent[field?.type] || ViewFilterTypeText
  }

  getCompatibleFieldTypes() {
    return [
      'text',
      'long_text',
      'url',
      'email',
      'number',
      'rating',
      'phone_number',
      'uuid',
      'autonumber',
      'duration',
      FormulaFieldType.compatibleWithFormulaTypes('text', 'char', 'number'),
    ]
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
    return [
      'file',
      FormulaFieldType.compatibleWithFormulaTypes(
        FormulaFieldType.arrayOf('single_file')
      ),
    ]
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
    const { i18n } = this.app
    return i18n.t('viewFilter.hasFileType')
  }

  getExample() {
    return 'image | document'
  }

  getInputComponent() {
    return ViewFilterTypeFileTypeDropdown
  }

  getCompatibleFieldTypes() {
    return [
      'file',
      FormulaFieldType.compatibleWithFormulaTypes(
        FormulaFieldType.arrayOf('single_file')
      ),
    ]
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

export class FilesLowerThanViewFilterType extends ViewFilterType {
  static getType() {
    return 'files_lower_than'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.filesLowerThan')
  }

  getExample() {
    return '2'
  }

  getInputComponent() {
    return ViewFilterTypeNumber
  }

  getCompatibleFieldTypes() {
    return ['file']
  }

  matches(rowValue, filterValue, field, fieldType) {
    return rowValue.length < parseInt(filterValue)
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

  getInputComponent(field) {
    const inputComponent = {
      [NumberFieldType.getType()]: ViewFilterTypeNumber,
    }
    return inputComponent[field?.type] || ViewFilterTypeText
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
      'multiple_select',
      'number',
      'autonumber',
      FormulaFieldType.compatibleWithFormulaTypes(
        'text',
        'char',
        'number',
        'date'
      ),
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

  getInputComponent(field) {
    const inputComponent = {
      [NumberFieldType.getType()]: ViewFilterTypeNumber,
    }
    return inputComponent[field?.type] || ViewFilterTypeText
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
      'multiple_select',
      'number',
      'autonumber',
      FormulaFieldType.compatibleWithFormulaTypes(
        'text',
        'char',
        'number',
        'date'
      ),
    ]
  }

  matches(rowValue, filterValue, field, fieldType) {
    return fieldType.notContainsFilter(rowValue, filterValue, field)
  }
}

export class ContainsWordViewFilterType extends ViewFilterType {
  static getType() {
    return 'contains_word'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.containsWord')
  }

  getInputComponent(field) {
    return ViewFilterTypeText
  }

  getCompatibleFieldTypes() {
    return [
      'text',
      'long_text',
      'url',
      'email',
      'single_select',
      'multiple_select',
      FormulaFieldType.compatibleWithFormulaTypes('text', 'char'),
    ]
  }

  matches(rowValue, filterValue, field, fieldType) {
    return fieldType.containsWordFilter(rowValue, filterValue, field)
  }
}

export class DoesntContainWordViewFilterType extends ContainsWordViewFilterType {
  static getType() {
    return 'doesnt_contain_word'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.doesntContainWord')
  }

  matches(rowValue, filterValue, field, fieldType) {
    return fieldType.doesntContainWordFilter(rowValue, filterValue, field)
  }
}

export class LengthIsLowerThanViewFilterType extends ViewFilterType {
  static getType() {
    return 'length_is_lower_than'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.lengthIsLowerThan')
  }

  getExample() {
    return '5'
  }

  getInputComponent() {
    return ViewFilterTypeNumber
  }

  getCompatibleFieldTypes() {
    return ['text', 'long_text', 'url', 'email', 'phone_number']
  }

  matches(rowValue, filterValue, field, fieldType) {
    return (
      isNaN(filterValue) ||
      rowValue === null ||
      filterValue === 0 ||
      rowValue.toString().length < filterValue
    )
  }
}

class LocalizedDateViewFilterType extends ViewFilterType {
  getSeparator() {
    return DATE_FILTER_TIMEZONE_VALUE_SEPARATOR
  }

  getDateFormat() {
    return 'YYYY-MM-DD'
  }

  getDefaultTimezone(field) {
    return field.date_force_timezone || moment.tz.guess()
  }

  splitTimezoneAndValue(value) {
    return splitTimezoneAndFilterValue(value, this.getSeparator())
  }

  prepareValue(value, field, filterChanged = false) {
    const [, filterValue] = this.splitTimezoneAndValue(value)
    const timezone = this.getDefaultTimezone(field)
    return value && !filterChanged ? value : `${timezone}?${filterValue}`
  }
}

export class DateEqualViewFilterType extends LocalizedDateViewFilterType {
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
    return [
      'date',
      'last_modified',
      'created_on',
      FormulaFieldType.compatibleWithFormulaTypes('date'),
    ]
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (rowValue === null) {
      return false
    }

    const [timezone, dateValue] = this.splitTimezoneAndValue(filterValue)
    const filterDate = moment.utc(dateValue, this.getDateFormat(), true)
    const rowDate = moment.utc(rowValue)
    if (timezone !== null) {
      filterDate.tz(timezone, true)
      rowDate.tz(timezone)
    }

    return dateValue === '' || rowDate.isSame(filterDate, 'date')
  }
}

export class DateNotEqualViewFilterType extends LocalizedDateViewFilterType {
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
    return [
      'date',
      'last_modified',
      'created_on',
      FormulaFieldType.compatibleWithFormulaTypes('date'),
    ]
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (rowValue === null) {
      return true
    }

    const [timezone, dateValue] = this.splitTimezoneAndValue(filterValue)
    const filterDate = moment.utc(dateValue, this.getDateFormat(), true)
    const rowDate = moment.utc(rowValue)

    if (timezone !== null) {
      filterDate.tz(timezone, true)
      rowDate.tz(timezone)
    }

    return dateValue === '' || !rowDate.isSame(filterDate, 'date')
  }
}

export class DateBeforeViewFilterType extends LocalizedDateViewFilterType {
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
    return [
      'date',
      'last_modified',
      'created_on',
      FormulaFieldType.compatibleWithFormulaTypes('date'),
    ]
  }

  matches(rowValue, filterValue, field, fieldType) {
    const [timezone, dateValue] = this.splitTimezoneAndValue(filterValue)
    const filterDate = moment.utc(dateValue, this.getDateFormat(), true)
    const rowDate = moment.utc(rowValue)

    // without a valid date the filter won't be applied
    if (!filterDate.isValid()) {
      return true
    }

    // an invalid date will be filtered out
    if (rowValue === null || !rowDate.isValid()) {
      return false
    }

    if (timezone !== null) {
      filterDate.tz(timezone, true)
      rowDate.tz(timezone)
    }

    return rowDate.isBefore(filterDate, 'day')
  }
}

export class DateBeforeOrEqualViewFilterType extends LocalizedDateViewFilterType {
  static getType() {
    return 'date_before_or_equal'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.isBeforeOrEqualDate')
  }

  getExample() {
    return '2020-01-01'
  }

  getInputComponent() {
    return ViewFilterTypeDate
  }

  getCompatibleFieldTypes() {
    return [
      'date',
      'last_modified',
      'created_on',
      FormulaFieldType.compatibleWithFormulaTypes('date'),
    ]
  }

  matches(rowValue, filterValue, field, fieldType) {
    const [timezone, dateValue] = this.splitTimezoneAndValue(filterValue)
    const filterDate = moment.utc(dateValue, this.getDateFormat(), true)
    const rowDate = moment.utc(rowValue)

    // without a valid date the filter won't be applied
    if (!filterDate.isValid()) {
      return true
    }

    // an invalid date will be filtered out
    if (rowValue === null || !rowDate.isValid()) {
      return false
    }

    if (timezone !== null) {
      filterDate.tz(timezone, true)
      rowDate.tz(timezone)
    }

    return rowDate.isSameOrBefore(filterDate, 'day')
  }
}

export class DateAfterViewFilterType extends LocalizedDateViewFilterType {
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
    return [
      'date',
      'last_modified',
      'created_on',
      FormulaFieldType.compatibleWithFormulaTypes('date'),
    ]
  }

  matches(rowValue, filterValue, field, fieldType) {
    const [timezone, dateValue] = this.splitTimezoneAndValue(filterValue)
    const filterDate = moment.utc(dateValue, this.getDateFormat(), true)
    const rowDate = moment.utc(rowValue)
    if (timezone !== null) {
      filterDate.tz(timezone, true)
      rowDate.tz(timezone)
    }

    // without a valid date the filter won't be applied
    if (!filterDate.isValid()) {
      return true
    }

    // an invalid date will be filtered out
    if (rowValue === null || !rowDate.isValid()) {
      return false
    }
    return rowDate.isAfter(filterDate, 'day')
  }
}
export class DateAfterDaysAgoViewFilterType extends LocalizedDateViewFilterType {
  static getType() {
    return 'date_after_days_ago'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.isAfterDaysAgo')
  }

  getExample() {
    return '20'
  }

  getInputComponent() {
    return ViewFilterTypeNumberWithTimeZone
  }

  getCompatibleFieldTypes() {
    return [
      'date',
      'last_modified',
      'created_on',
      FormulaFieldType.compatibleWithFormulaTypes('date'),
    ]
  }

  matches(rowValue, filterValue) {
    if (rowValue === null || !moment.utc(rowValue).isValid()) {
      return false
    }

    const [timezone, rawDaysAgo] = this.splitTimezoneAndValue(filterValue)
    const daysAgo = parseInt(rawDaysAgo, 10)

    if (isNaN(daysAgo)) {
      return false
    }

    // Convert rowValue to a date object and adjust to timezone if provided.
    let rowDate = moment.utc(rowValue)
    if (timezone !== null) {
      rowDate = rowDate.tz(timezone)
    }

    // Create a date object for current date and adjust to timezone if provided.
    let now = moment.utc()
    if (timezone !== null) {
      now = now.tz(timezone)
    }

    // Calculate the date daysAgo days from now.
    const daysAgoDate = now.subtract(daysAgo, 'days')

    // Check if rowDate is the same as or after daysAgoDate.
    return rowDate.isSameOrAfter(daysAgoDate, 'day')
  }
}

export class DateAfterOrEqualViewFilterType extends LocalizedDateViewFilterType {
  static getType() {
    return 'date_after_or_equal'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.isAfterOrEqualDate')
  }

  getExample() {
    return '2020-01-01'
  }

  getInputComponent() {
    return ViewFilterTypeDate
  }

  getCompatibleFieldTypes() {
    return [
      'date',
      'last_modified',
      'created_on',
      FormulaFieldType.compatibleWithFormulaTypes('date'),
    ]
  }

  matches(rowValue, filterValue, field, fieldType) {
    const [timezone, dateValue] = this.splitTimezoneAndValue(filterValue)
    const filterDate = moment.utc(dateValue, this.getDateFormat(), true)
    const rowDate = moment.utc(rowValue)
    if (timezone !== null) {
      filterDate.tz(timezone, true)
      rowDate.tz(timezone)
    }

    // without a valid date the filter won't be applied
    if (!filterDate.isValid()) {
      return true
    }

    // an invalid date will be filtered out
    if (rowValue === null || !rowDate.isValid()) {
      return false
    }
    return rowDate.isSameOrAfter(filterDate, 'day')
  }
}

/**
 * Base class for compare dates with today.
 */
export class DateCompareTodayViewFilterType extends LocalizedDateViewFilterType {
  static getType() {
    throw new Error('Not implemented')
  }

  getName() {
    throw new Error('Not implemented')
  }

  isDateMatching(rowValue, today) {
    throw new Error('Not implemented')
  }

  getInputComponent() {
    return ViewFilterTypeTimeZone
  }

  getCompatibleFieldTypes() {
    return [
      'date',
      'last_modified',
      'created_on',
      FormulaFieldType.compatibleWithFormulaTypes('date'),
    ]
  }

  getDefaultValue(field) {
    return this.getDefaultTimezone(field)
  }

  prepareValue(value, field, filterChanged = false) {
    return value && !filterChanged ? value : `${this.getDefaultValue(field)}?`
  }

  getExample() {
    return 'UTC'
  }

  matches(rowValue, filterValue, field) {
    if (rowValue === null || !moment.utc(rowValue).isValid()) {
      return false
    }

    const [timezone] = this.splitTimezoneAndValue(filterValue)

    const rowDate = moment.utc(rowValue)
    const today = moment.utc()
    if (timezone !== null) {
      today.tz(timezone)
      rowDate.tz(timezone)
    }
    return this.isDateMatching(rowDate, today)
  }
}

export class DateEqualsTodayViewFilterType extends DateCompareTodayViewFilterType {
  static getType() {
    return 'date_equals_today'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.isToday')
  }

  get hasEditableValue() {
    return false
  }

  isDateMatching(rowValue, today) {
    const minTime = today.clone().startOf('day')
    const maxtime = today.clone().endOf('day')
    return rowValue.isBetween(minTime, maxtime, null, '[]')
  }
}

export class DateBeforeTodayViewFilterType extends DateCompareTodayViewFilterType {
  static getType() {
    return 'date_before_today'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.beforeToday')
  }

  get hasEditableValue() {
    return false
  }

  isDateMatching(rowValue, today) {
    const minTime = today.clone().startOf('day')
    return rowValue.isBefore(minTime)
  }
}

export class DateAfterTodayViewFilterType extends DateCompareTodayViewFilterType {
  static getType() {
    return 'date_after_today'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.afterToday')
  }

  get hasEditableValue() {
    return false
  }

  isDateMatching(rowValue, today) {
    const maxtime = today.clone().endOf('day')
    return rowValue.isAfter(maxtime)
  }
}

export class DateEqualsCurrentWeekViewFilterType extends DateCompareTodayViewFilterType {
  static getType() {
    return 'date_equals_week'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.inThisWeek')
  }

  isDateMatching(rowValue, today) {
    const firstDay = today.clone().startOf('isoWeek')
    const lastDay = today.clone().endOf('isoWeek')
    return rowValue.isBetween(firstDay, lastDay, null, '[]')
  }
}

export class DateEqualsCurrentMonthViewFilterType extends DateCompareTodayViewFilterType {
  static getType() {
    return 'date_equals_month'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.inThisMonth')
  }

  isDateMatching(rowValue, today) {
    const firstDay = today.clone().startOf('month')
    const lastDay = today.clone().endOf('month')
    return rowValue.isBetween(firstDay, lastDay, null, '[]')
  }
}

export class DateEqualsCurrentYearViewFilterType extends DateEqualsTodayViewFilterType {
  static getType() {
    return 'date_equals_year'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.inThisYear')
  }

  isDateMatching(rowValue, today) {
    const firstDay = today.clone().startOf('year')
    const lastDay = today.clone().endOf('year')
    return rowValue.isBetween(firstDay, lastDay, null, '[]')
  }
}

/**
 * Base class for days, months, years ago filters.
 */
export class LocalizedDateCompareViewFilterType extends LocalizedDateViewFilterType {
  getInputComponent() {
    return ViewFilterTypeNumberWithTimeZone
  }

  getCompatibleFieldTypes() {
    return [
      'date',
      'last_modified',
      'created_on',
      FormulaFieldType.compatibleWithFormulaTypes('date'),
    ]
  }

  getExample() {
    const tzone = moment.tz.guess()
    const xAgo = 1
    return `${tzone}${this.getSeparator()}${xAgo}`
  }

  splitTimezoneAndXToCompare(field, rawValue) {
    const [timezone, value] = this.splitTimezoneAndValue(rawValue)

    let filterValue = value
    if (filterValue !== null) {
      filterValue = parseInt(filterValue)
    }

    filterValue = isNaN(filterValue) ? '' : filterValue
    return [timezone, filterValue]
  }

  getValidNumberWithTimezone(rawValue, field) {
    const [timezone, filterValue] = this.splitTimezoneAndXToCompare(
      field,
      rawValue
    )
    return `${timezone}${this.getSeparator()}${filterValue}`
  }

  getDefaultValue(field) {
    return this.getValidNumberWithTimezone(null, field)
  }

  prepareValue(value, field) {
    return this.getValidNumberWithTimezone(value, field)
  }

  getDateToCompare(xToCompare) {
    throw new Error('Not implemented')
  }

  isDateMatching(rowValue, dateToCompare, today) {
    throw new Error('Not implemented')
  }

  matches(rowValue, filterValue, field) {
    if (rowValue === null) {
      rowValue = ''
    }

    const [timezone, xToCompare] = this.splitTimezoneAndXToCompare(
      field,
      filterValue
    )

    // an invalid daysAgo will result in an empty filter
    if (xToCompare === '') {
      return true
    }

    let dateToCompare
    try {
      dateToCompare = this.getDateToCompare(xToCompare)
    } catch (e) {
      return false
    }

    const rowDate = moment.utc(rowValue)
    const today = moment.utc()
    if (timezone) {
      dateToCompare.tz(timezone)
      rowDate.tz(timezone)
      today.tz(timezone)
    }
    return this.isDateMatching(rowDate, dateToCompare, today)
  }
}

function isRowValueBetweenDays(rowValue, dateToCompare, today) {
  const [firstDay, lastDay] = dateToCompare.isSameOrBefore(today)
    ? [dateToCompare, today]
    : [today, dateToCompare]
  return rowValue.isBetween(firstDay, lastDay, 'days', '[]')
}

export class DateWithinDaysViewFilterType extends LocalizedDateCompareViewFilterType {
  static getType() {
    return 'date_within_days'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.isWithinDays')
  }

  getDateToCompare(xToCompare) {
    return moment.utc().add(parseInt(xToCompare), 'days')
  }

  isDateMatching(rowValue, dateToCompare, today) {
    return isRowValueBetweenDays(rowValue, dateToCompare, today)
  }
}

export class DateWithinWeeksViewFilterType extends LocalizedDateCompareViewFilterType {
  static getType() {
    return 'date_within_weeks'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.isWithinWeeks')
  }

  getDateToCompare(xToCompare) {
    const numberOfWeeks = parseInt(xToCompare)
    if (numberOfWeeks === 0) {
      throw new Error('Number of weeks cannot be 0')
    }
    return moment.utc().add(numberOfWeeks, 'weeks')
  }

  isDateMatching(rowValue, dateToCompare, today) {
    return isRowValueBetweenDays(rowValue, dateToCompare, today)
  }
}

export class DateWithinMonthsViewFilterType extends LocalizedDateCompareViewFilterType {
  static getType() {
    return 'date_within_months'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.isWithinMonths')
  }

  getDateToCompare(xToCompare) {
    const numberOfMonths = parseInt(xToCompare)
    if (numberOfMonths === 0) {
      throw new Error('Number of months cannot be 0')
    }
    return moment.utc().add(numberOfMonths, 'month')
  }

  isDateMatching(rowValue, dateToCompare, today) {
    return isRowValueBetweenDays(rowValue, dateToCompare, today)
  }
}

export class DateEqualsDaysAgoViewFilterType extends LocalizedDateCompareViewFilterType {
  static getType() {
    return 'date_equals_days_ago'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.isDaysAgo')
  }

  getDateToCompare(xToCompare) {
    return moment.utc().subtract(parseInt(xToCompare), 'days')
  }

  isDateMatching(rowValue, dateToCompare, today) {
    return rowValue.isSame(dateToCompare, 'day')
  }
}

export class DateEqualsMonthsAgoViewFilterType extends LocalizedDateCompareViewFilterType {
  static getType() {
    return 'date_equals_months_ago'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.isMonthsAgo')
  }

  getDateToCompare(xToCompare) {
    return moment.utc().subtract(parseInt(xToCompare), 'months')
  }

  isDateMatching(rowValue, dateToCompare, today) {
    return rowValue.isSame(dateToCompare, 'month')
  }
}

export class DateEqualsYearsAgoViewFilterType extends LocalizedDateCompareViewFilterType {
  static getType() {
    return 'date_equals_years_ago'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.isYearsAgo')
  }

  getDateToCompare(xToCompare) {
    return moment.utc().subtract(parseInt(xToCompare), 'years')
  }

  isDateMatching(rowValue, dateToCompare, today) {
    return rowValue.isSame(dateToCompare, 'year')
  }
}

export class DateEqualsDayOfMonthViewFilterType extends LocalizedDateViewFilterType {
  static getType() {
    return 'date_equals_day_of_month'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.isDayOfMonth')
  }

  getExample() {
    return '1'
  }

  getInputComponent() {
    return ViewFilterTypeNumberWithTimeZone
  }

  isDateMatching(rowValue, dayOfMonth) {
    return rowValue.date() === dayOfMonth
  }

  getCompatibleFieldTypes() {
    return ['date', 'last_modified', 'created_on']
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (rowValue === null) {
      rowValue = ''
    }

    const [timezone, rawDayOfMonth] = this.splitTimezoneAndValue(filterValue)
    if (rawDayOfMonth === '') {
      return true
    }

    // an invalid daysAgo will result in an empty filter
    const dayOfMonth = parseInt(rawDayOfMonth)
    if (isNaN(dayOfMonth) || dayOfMonth < 1 || dayOfMonth > 31) {
      return false
    }

    let rowDate = moment.utc(rowValue)
    if (timezone !== null) {
      rowDate = rowDate.tz(timezone)
    }
    return this.isDateMatching(rowDate, dayOfMonth)
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

  getInputComponent(field) {
    const inputComponent = {
      [RatingFieldType.getType()]: ViewFilterTypeRating,
      [DurationFieldType.getType()]: ViewFilterTypeDuration,
    }
    return inputComponent[field?.type] || ViewFilterTypeNumber
  }

  getCompatibleFieldTypes() {
    return [
      'number',
      'rating',
      'autonumber',
      'duration',
      FormulaFieldType.compatibleWithFormulaTypes('number'),
    ]
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (filterValue === '') {
      return true
    }

    const rowVal = fieldType.parseInputValue(field, rowValue)
    const fltVal = fieldType.parseInputValue(field, filterValue)
    return Number.isFinite(rowVal) && Number.isFinite(fltVal) && rowVal > fltVal
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

  getInputComponent(field) {
    const inputComponent = {
      [RatingFieldType.getType()]: ViewFilterTypeRating,
      [DurationFieldType.getType()]: ViewFilterTypeDuration,
    }
    return inputComponent[field?.type] || ViewFilterTypeNumber
  }

  getCompatibleFieldTypes() {
    return [
      'number',
      'rating',
      'autonumber',
      'duration',
      FormulaFieldType.compatibleWithFormulaTypes('number'),
    ]
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (filterValue === '') {
      return true
    }

    const rowVal = fieldType.parseInputValue(field, rowValue)
    const fltVal = fieldType.parseInputValue(field, filterValue)
    return Number.isFinite(rowVal) && Number.isFinite(fltVal) && rowVal < fltVal
  }
}

export class IsEvenAndWholeViewFilterType extends ViewFilterType {
  static getType() {
    return 'is_even_and_whole'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.isEvenAndWhole')
  }

  getExample() {
    return 'true'
  }

  get hasEditableValue() {
    return false
  }

  getCompatibleFieldTypes() {
    return [
      'number',
      'autonumber',
      FormulaFieldType.compatibleWithFormulaTypes('number'),
    ]
  }

  matches(rowValue, filterValue, field, fieldType) {
    rowValue = parseFloat(rowValue)
    return rowValue % 2 === 0 && Number.isInteger(rowValue)
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

export class MultipleSelectHasFilterType extends ViewFilterType {
  static getType() {
    return 'multiple_select_has'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.has')
  }

  getExample() {
    return '1'
  }

  getInputComponent() {
    return ViewFilterTypeSelectOptions
  }

  getCompatibleFieldTypes() {
    return ['multiple_select']
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (!isNumeric(filterValue)) {
      return true
    }

    const filterValueId = parseInt(filterValue)
    return rowValue.some((option) => option.id === filterValueId)
  }
}

export class MultipleSelectHasNotFilterType extends ViewFilterType {
  static getType() {
    return 'multiple_select_has_not'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.hasNot')
  }

  getExample() {
    return '1'
  }

  getInputComponent() {
    return ViewFilterTypeSelectOptions
  }

  getCompatibleFieldTypes() {
    return ['multiple_select']
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (!isNumeric(filterValue)) {
      return true
    }

    const filterValueId = parseInt(filterValue)
    return !rowValue.some((option) => option.id === filterValueId)
  }
}

export class MultipleCollaboratorsHasFilterType extends ViewFilterType {
  static getType() {
    return 'multiple_collaborators_has'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.has')
  }

  getExample() {
    return '1'
  }

  getInputComponent() {
    return ViewFilterTypeCollaborators
  }

  getCompatibleFieldTypes() {
    return ['multiple_collaborators']
  }

  isAllowedInPublicViews() {
    return false
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (!isNumeric(filterValue)) {
      return true
    }

    const filterValueId = parseInt(filterValue)
    return rowValue.some((user) => user.id === filterValueId)
  }
}

export class MultipleCollaboratorsHasNotFilterType extends ViewFilterType {
  static getType() {
    return 'multiple_collaborators_has_not'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.hasNot')
  }

  getExample() {
    return '1'
  }

  getInputComponent() {
    return ViewFilterTypeCollaborators
  }

  getCompatibleFieldTypes() {
    return ['multiple_collaborators']
  }

  isAllowedInPublicViews() {
    return false
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (!isNumeric(filterValue)) {
      return true
    }

    const filterValueId = parseInt(filterValue)
    return !rowValue.some((user) => user.id === filterValueId)
  }
}

export class UserIsFilterType extends ViewFilterType {
  static getType() {
    return 'user_is'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.is')
  }

  getExample() {
    return '1'
  }

  getInputComponent() {
    return ViewFilterTypeCollaborators
  }

  getCompatibleFieldTypes() {
    return ['created_by', 'last_modified_by']
  }

  isAllowedInPublicViews() {
    return false
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (!isNumeric(filterValue)) {
      return true
    }

    const filterValueId = parseInt(filterValue)
    return rowValue?.id === filterValueId
  }
}

export class UserIsNotFilterType extends ViewFilterType {
  static getType() {
    return 'user_is_not'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.isNot')
  }

  getExample() {
    return '1'
  }

  getInputComponent() {
    return ViewFilterTypeCollaborators
  }

  getCompatibleFieldTypes() {
    return ['created_by', 'last_modified_by']
  }

  isAllowedInPublicViews() {
    return false
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (!isNumeric(filterValue)) {
      return true
    }

    const filterValueId = parseInt(filterValue)
    return rowValue?.id !== filterValueId
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
    return ['boolean', FormulaFieldType.compatibleWithFormulaTypes('boolean')]
  }

  matches(rowValue, filterValue, field, fieldType) {
    filterValue = trueValues.includes(
      filterValue.toString().toLowerCase().trim()
    )

    if (rowValue === null) {
      rowValue = false
    } else {
      rowValue = trueValues.includes(rowValue.toString().toLowerCase().trim())
    }
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

export class LinkRowContainsFilterType extends ViewFilterType {
  static getType() {
    return 'link_row_contains'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.contains')
  }

  getExample() {
    return 'string'
  }

  getInputComponent() {
    return ViewFilterTypeText
  }

  getCompatibleFieldTypes() {
    return ['link_row']
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (filterValue === '') {
      return true
    }

    return rowValue.some(
      ({ value }) => value.search(new RegExp(filterValue, 'i')) !== -1
    )
  }
}

export class LinkRowNotContainsFilterType extends ViewFilterType {
  static getType() {
    return 'link_row_not_contains'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewFilter.containsNot')
  }

  getExample() {
    return 'string'
  }

  getInputComponent() {
    return ViewFilterTypeText
  }

  getCompatibleFieldTypes() {
    return ['link_row']
  }

  matches(rowValue, filterValue, field, fieldType) {
    if (filterValue === '') {
      return true
    }

    return !rowValue.some(
      ({ value }) => value.search(new RegExp(filterValue, 'i')) !== -1
    )
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

  get hasEditableValue() {
    return false
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
      'multiple_select',
      'multiple_collaborators',
      'phone_number',
      'duration',
      'password',
      FormulaFieldType.compatibleWithFormulaTypes(
        'text',
        'char',
        'boolean',
        'date',
        'number',
        FormulaFieldType.arrayOf('single_file')
      ),
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

  get hasEditableValue() {
    return false
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
      'multiple_select',
      'multiple_collaborators',
      'phone_number',
      'duration',
      'password',
      FormulaFieldType.compatibleWithFormulaTypes(
        'text',
        'char',
        'boolean',
        'date',
        'number',
        FormulaFieldType.arrayOf('single_file')
      ),
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
