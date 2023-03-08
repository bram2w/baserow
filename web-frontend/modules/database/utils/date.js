import moment from '@baserow/modules/core/moment'

const dateMapping = {
  EU: {
    momentFormat: 'DD/MM/YYYY',
    humanFormat: 'dd/mm/yyyy',
  },
  US: {
    momentFormat: 'MM/DD/YYYY',
    humanFormat: 'mm/dd/yyyy',
  },
  ISO: {
    momentFormat: 'YYYY-MM-DD',
    humanFormat: 'yyyy-mm-dd',
  },
}

const timeMapping = {
  12: {
    momentFormat: 'hh:mm A',
    humanFormat: 'hh:mm AM',
  },
  24: {
    momentFormat: 'HH:mm',
    humanFormat: 'hh:mm',
  },
}

export const getDateMomentFormat = (type) => {
  if (!Object.prototype.hasOwnProperty.call(dateMapping, type)) {
    throw new Error(`${type} wasn't found in the date mapping.`)
  }
  return dateMapping[type].momentFormat
}

export const getTimeMomentFormat = (type) => {
  if (!Object.prototype.hasOwnProperty.call(timeMapping, type)) {
    throw new Error(`${type} wasn't found in the time mapping.`)
  }
  return timeMapping[type].momentFormat
}

export const getDateHumanReadableFormat = (type) => {
  if (!Object.prototype.hasOwnProperty.call(dateMapping, type)) {
    throw new Error(`${type} wasn't found in the date mapping.`)
  }
  return dateMapping[type].humanFormat
}

export const getTimeHumanReadableFormat = (type) => {
  if (!Object.prototype.hasOwnProperty.call(timeMapping, type)) {
    throw new Error(`${type} wasn't found in the time mapping.`)
  }
  return timeMapping[type].humanFormat
}

/**
 * Returns the timezone for a given field. If the field doesn't have a timezone
 * set, the timezone of the user is returned.
 *
 * @param {Object} field The field object
 * @returns {String} The timezone for the field
 * @example
 * getFieldTimezone({ date_include_time: true, date_force_timezone: 'Europe/Amsterdam' }) // => 'Europe/Amsterdam'
 * getFieldTimezone({ date_include_time: false }) // => 'UTC'
 */
export const getFieldTimezone = (field) => {
  return field.date_include_time
    ? field.date_force_timezone || moment.tz.guess()
    : null
}

/**
 * Returns the timezone abbreviation for a given field and value.
 * If the value is null or undefined and force=false, an empty string is returned.
 *
 * @param {Object} field The field object
 * @param {String | moment} value The value to parse into a moment object
 * @param {Object} options
 * @param {String} options.format The format to parse the value with
 * @param {Boolean} options.replace Whether to replace the timezone or not
 */
export const getCellTimezoneAbbr = (
  field,
  value,
  { format = 'z', force = false } = {}
) => {
  if (!force && (value === null || value === undefined)) {
    return ''
  }
  const timezone = getFieldTimezone(field)

  return timezone
    ? moment
        .utc(value || undefined)
        .tz(timezone)
        .format(format)
    : 'UTC'
}

/**
 * Returns a moment object with the correct timezone set.
 *
 * @param {Object} field The field object
 * @param {String | moment} value The value to parse into a moment object
 * @param {Object} options
 * @param {String} options.format The format to parse the value with
 * @param {Boolean} options.replace Whether to replace the timezone or not
 * @returns {moment} The moment object
 */
export const localizeMoment = (field, value, { format = undefined } = {}) => {
  const timezone = getFieldTimezone(field)

  const date = moment.utc(value, format, true /** strict */)
  return timezone !== null
    ? date.utcOffset(moment.tz(timezone)).tz(timezone, true)
    : date
}

export const DATE_FILTER_TIMEZONE_VALUE_SEPARATOR = '?'

/**
 * Splits the timezone and the filter value from a filter value.
 *
 * @param {*} value  The filter value
 * @param {*} separator  The separator between the timezone and the filter value
 * @returns {Array}  An array with the timezone and the filter value
 */
export const splitTimezoneAndFilterValue = (
  value,
  separator = DATE_FILTER_TIMEZONE_VALUE_SEPARATOR
) => {
  let timezone = null
  let filterValue

  if (value.includes(separator)) {
    // if the filter value already contains a timezone, use it
    ;[timezone, filterValue] = value.split(separator)
  } else {
    // fallback for values before timezone was added to the filter value
    filterValue = value
  }
  timezone = moment.tz.zone(timezone) ? timezone : null
  return [timezone, filterValue]
}
