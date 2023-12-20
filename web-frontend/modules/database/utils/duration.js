const MOST_ACCURATE_DURATION_FORMAT = 'h:mm:ss.sss'
const MAX_NUMBER_OF_TOKENS_IN_DURATION_FORMAT =
  MOST_ACCURATE_DURATION_FORMAT.split(':').length
export const MAX_BACKEND_DURATION_VALUE_NUMBER_OF_SECS = 86400000000000 // taken from backend timedelta.max.total_seconds()

// Map guarantees the order of the entries
export const DURATION_FORMATS = new Map([
  [
    'h:mm',
    {
      description: 'h:mm (1:23)',
      example: '1:23',
      toString(hours, minutes) {
        return `${hours}:${minutes.toString().padStart(2, '0')}`
      },
      round: (value) => Math.round(value / 60) * 60,
    },
  ],
  [
    'h:mm:ss',
    {
      description: 'h:mm:ss (1:23:40)',
      example: '1:23:40',
      toString(hours, minutes, seconds) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds
          .toString()
          .padStart(2, '0')}`
      },
      round: (value) => Math.round(value),
    },
  ],
  [
    'h:mm:ss.s',
    {
      description: 'h:mm:ss.s (1:23:40.0)',
      example: '1:23:40.0',
      toString(hours, minutes, seconds) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds
          .toFixed(1)
          .padStart(4, '0')}`
      },
      round: (value) => Math.round(value * 10) / 10,
    },
  ],
  [
    'h:mm:ss.ss',
    {
      description: 'h:mm:ss.ss (1:23:40.00)',
      example: '1:23:40.00',
      toString(hours, minutes, seconds) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds
          .toFixed(2)
          .padStart(5, '0')}`
      },
      round: (value) => Math.round(value * 100) / 100,
    },
  ],
  [
    'h:mm:ss.sss',
    {
      description: 'h:mm:ss.sss (1:23:40.000)',
      example: '1:23:40.000',
      toString(hours, minutes, seconds) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds
          .toFixed(3)
          .padStart(6, '0')}`
      },
      round: (value) => Math.round(value * 1000) / 1000,
    },
  ],
])

export const DURATION_TOKENS = {
  h: {
    multiplier: 3600,
    parse: (value) => parseInt(value),
  },
  mm: {
    multiplier: 60,
    parse: (value) => parseInt(value),
  },
  ss: {
    multiplier: 1,
    parse: (value) => parseInt(value),
  },
  'ss.s': {
    multiplier: 1,
    parse: (value) => Math.round(parseFloat(value) * 10) / 10,
  },
  'ss.ss': {
    multiplier: 1,
    parse: (value) => Math.round(parseFloat(value) * 100) / 100,
  },
  'ss.sss': {
    multiplier: 1,
    parse: (value) => Math.round(parseFloat(value) * 1000) / 1000,
  },
}

export const roundDurationValueToFormat = (value, format) => {
  if (value === null) {
    return null
  }

  const roundFunc = DURATION_FORMATS.get(format).round
  return roundFunc(value)
}

/**
 * It tries to parse the input value using the given format.
 * If the input value does not match the format, it tries to parse it using
 * the most accurate format if strict is false, otherwise it throws an error.
 */
export const parseDurationValue = (
  inputValue,
  format = MOST_ACCURATE_DURATION_FORMAT,
  strict = false
) => {
  if (inputValue === null || inputValue === undefined || inputValue === '') {
    return null
  }

  // If the input value is a number, we assume it is in seconds.
  if (Number.isFinite(inputValue)) {
    return inputValue > 0 ? inputValue : null
  }

  const parts = inputValue.split(':').reverse()
  let tokens = format.split(':').reverse()
  if (parts.length > tokens.length) {
    if (strict || parts.length > MAX_NUMBER_OF_TOKENS_IN_DURATION_FORMAT) {
      throw new Error(
        `Invalid duration format: ${inputValue} does not match ${format}`
      )
    } else {
      tokens = MOST_ACCURATE_DURATION_FORMAT.split(':').reverse()
    }
  }

  try {
    return tokens.reduce((acc, token, index) => {
      if (index >= parts.length) {
        return acc
      }
      const part = parts[index]
      const parseFunc = DURATION_TOKENS[token].parse
      const number = parseFunc(part)

      if (isNaN(number) || number < 0) {
        throw new Error(
          `Invalid duration format: ${inputValue} does not match ${format}`
        )
      }

      const multiplier = DURATION_TOKENS[token].multiplier
      return acc + number * multiplier
    }, 0)
  } catch (e) {
    return null
  }
}

/**
 * It formats the given duration value using the given format.
 */
export const formatDuration = (value, format) => {
  if (value === null || value === undefined || value === '') {
    return ''
  }

  const hours = Math.floor(value / 3600)
  const mins = Math.floor((value - hours * 3600) / 60)
  const secs = value - hours * 3600 - mins * 60

  const formatFunc = DURATION_FORMATS.get(format).toString
  return formatFunc(hours, mins, secs)
}
