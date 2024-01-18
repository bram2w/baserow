const MOST_ACCURATE_DURATION_FORMAT = 'h:mm:ss.sss'
// taken from backend timedelta.max.total_seconds() == 1_000_000_000 days
export const MAX_BACKEND_DURATION_VALUE_NUMBER_OF_SECS = 86400000000000
export const DEFAULT_DURATION_FORMAT = 'h:mm'

const D_H = 'd h'
const D_H_M = 'd h:mm'
const D_H_M_S = 'd h:mm:ss'
const H_M = 'h:mm'
const H_M_S = 'h:mm:ss'
const H_M_S_S = 'h:mm:ss.s'
const H_M_S_SS = 'h:mm:ss.ss'
const H_M_S_SSS = 'h:mm:ss.sss'

const SECS_IN_DAY = 86400
const SECS_IN_HOUR = 3600
const SECS_IN_MIN = 60

function totalSecs({ secs = 0, mins = 0, hours = 0, days = 0 }) {
  return (
    parseInt(days) * SECS_IN_DAY +
    parseInt(hours) * SECS_IN_HOUR +
    parseInt(mins) * SECS_IN_MIN +
    parseFloat(secs)
  )
}

const DURATION_REGEXPS = new Map([
  [
    /^(\d+)(?:d\s*|\s+)(\d+):(\d+):(\d+|\d+\.\d+)$/,
    {
      default: (days, hours, mins, secs) =>
        totalSecs({ days, hours, mins, secs }),
    },
  ],
  [
    /^(\d+):(\d+):(\d+|\d+\.\d+)$/,
    {
      default: (hours, mins, secs) => totalSecs({ hours, mins, secs }),
    },
  ],
  [
    /^(\d+)(?:d\s*|\s+)(\d+):(\d+)$/,
    {
      [D_H]: (days, hours, mins) => totalSecs({ days, hours, mins }),
      [D_H_M]: (days, hours, mins) => totalSecs({ days, hours, mins }),
      default: (days, mins, secs) => totalSecs({ days, mins, secs }),
    },
  ],
  [
    /^(\d+)(?:d\s*|\s+)(\d+):(\d+\.\d+)$/,
    { default: (days, mins, secs) => totalSecs({ days, mins, secs }) },
  ],
  [/^(\d+)h$/, { default: (hours) => totalSecs({ hours }) }],
  [
    /^(\d+)(?:d\s*|\s+)(\d+)h$/,
    {
      default: (days, hours) => totalSecs({ days, hours }),
    },
  ],
  [/^(\d+)d$/, { default: (days) => totalSecs({ days }) }],
  [
    /^(\d+)(?:d\s*|\s+)(\d+)$/,
    {
      [D_H]: (days, hours) => totalSecs({ days, hours }),
      [D_H_M]: (days, mins) => totalSecs({ days, mins }),
      [H_M]: (days, mins) => totalSecs({ days, mins }),
      default: (days, secs) => totalSecs({ days, secs }),
    },
  ],
  [
    /^(\d+)(?:d\s*|\s+)(\d+\.\d+)$/,
    { default: (days, secs) => totalSecs({ days, secs }) },
  ],
  [
    /^(\d+):(\d+)$/,
    {
      [D_H]: (hours, mins) => totalSecs({ hours, mins }),
      [D_H_M]: (hours, mins) => totalSecs({ hours, mins }),
      [H_M]: (hours, mins) => totalSecs({ hours, mins }),
      default: (mins, secs) => totalSecs({ mins, secs }),
    },
  ],
  [
    /^(\d+):(\d+\.\d+)$/,
    { default: (mins, secs) => totalSecs({ mins, secs }) },
  ],
  [/^(\d+\.\d+)$/, { default: (secs) => totalSecs({ secs }) }],
  [
    /^(\d+)$/,
    {
      [D_H]: (hours) => totalSecs({ hours }),
      [D_H_M]: (mins) => totalSecs({ mins }),
      [H_M]: (mins) => totalSecs({ mins }),
      default: (secs) => totalSecs({ secs }),
    },
  ],
])

// Map guarantees the order of the entries
export const DURATION_FORMATS = new Map([
  [
    H_M,
    {
      description: 'h:mm (1:23)',
      example: '1:23',
      toString(d, h, m, s) {
        return `${d * 24 + h}:${m.toString().padStart(2, '0')}`
      },
      round: (value) => Math.round(value / 60) * 60,
    },
  ],
  [
    H_M_S,
    {
      description: 'h:mm:ss (1:23:40)',
      example: '1:23:40',
      toString(d, h, m, s) {
        return `${d * 24 + h}:${m.toString().padStart(2, '0')}:${s
          .toString()
          .padStart(2, '0')}`
      },
      round: (value) => Math.round(value),
    },
  ],
  [
    H_M_S_S,
    {
      description: 'h:mm:ss.s (1:23:40.0)',
      example: '1:23:40.0',
      toString(d, h, m, s) {
        return `${d * 24 + h}:${m.toString().padStart(2, '0')}:${s
          .toFixed(1)
          .padStart(4, '0')}`
      },
      round: (value) => Math.round(value * 10) / 10,
    },
  ],
  [
    H_M_S_SS,
    {
      description: 'h:mm:ss.ss (1:23:40.00)',
      example: '1:23:40.00',
      toString(d, h, m, s) {
        return `${d * 24 + h}:${m.toString().padStart(2, '0')}:${s
          .toFixed(2)
          .padStart(5, '0')}`
      },
      round: (value) => Math.round(value * 100) / 100,
    },
  ],
  [
    H_M_S_SSS,
    {
      description: 'h:mm:ss.sss (1:23:40.000)',
      example: '1:23:40.000',
      toString(d, h, m, s) {
        return `${d * 24 + h}:${m.toString().padStart(2, '0')}:${s
          .toFixed(3)
          .padStart(6, '0')}`
      },
      round: (value) => Math.round(value * 1000) / 1000,
    },
  ],
  [
    D_H,
    {
      description: 'd h (1d 2h)',
      example: '1d 2h',
      toString(d, h, m, s) {
        return `${d}d ${h}h`
      },
      round: (value) => Math.round(value / 3600) * 3600,
    },
  ],
  [
    D_H_M,
    {
      description: 'd h:mm (1d 2:34)',
      example: '1d 2:34',
      toString(d, h, m, s) {
        return `${d}d ${h}:${m.toString().padStart(2, '0')}`
      },
      round: (value) => Math.round(value / 60) * 60,
    },
  ],
  [
    D_H_M_S,
    {
      description: 'd h:mm:ss (1d 2:34:56)',
      example: '1d 2:34:56',
      toString(d, h, m, s) {
        return `${d}d ${h}:${m.toString().padStart(2, '0')}:${s
          .toString()
          .padStart(2, '0')}`
      },
      round: (value) => Math.round(value),
    },
  ],
])

export const roundDurationValueToFormat = (value, format) => {
  if (value === null) {
    return null
  }

  const durationFormatOptions = DURATION_FORMATS.get(format)
  if (!durationFormatOptions) {
    throw new Error(`Unknown duration format ${format}`)
  }
  return durationFormatOptions.round(value)
}

/**
 * It tries to parse the input value using the given format.
 * If the input value does not match the format, it tries to parse it using
 * the most accurate format if strict is false, otherwise it throws an error.
 */
export const parseDurationValue = (
  inputValue,
  format = MOST_ACCURATE_DURATION_FORMAT
) => {
  if (inputValue === null || inputValue === undefined || inputValue === '') {
    return null
  }

  // If the value is a number, we assume it's already in seconds (i.e. from the backend).
  if (Number.isFinite(inputValue)) {
    return inputValue > 0 ? inputValue : null
  }

  for (const [fmtRegExp, formatFuncs] of DURATION_REGEXPS) {
    const match = inputValue.match(fmtRegExp)
    if (match) {
      const formatFunc = formatFuncs[format] || formatFuncs.default
      return formatFunc(...match.slice(1))
    }
  }
  return null
}

/**
 * It formats the given duration value using the given format.
 */
export const formatDurationValue = (value, format) => {
  if (value === null || value === undefined || value === '') {
    return ''
  }

  const days = Math.floor(value / 86400)
  const hours = Math.floor((value % 86400) / 3600)
  const mins = Math.floor((value % 3600) / 60)
  const secs = value % 60

  const formatFunc = DURATION_FORMATS.get(format).toString
  return formatFunc(days, hours, mins, secs)
}
