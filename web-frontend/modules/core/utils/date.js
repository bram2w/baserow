import moment from '@baserow/modules/core/moment'

export const getHumanPeriodAgoCount = (dateTime) => {
  const now = moment()
  const d = moment(dateTime)

  const diffYears = now.diff(d, 'years')
  if (diffYears >= 1) {
    return {
      period: 'years',
      count: diffYears,
    }
  }

  const diffMonths = now.diff(d, 'months')
  if (diffMonths >= 1) {
    return {
      period: 'months',
      count: diffMonths,
    }
  }

  const diffDays = now.diff(d, 'days')
  if (diffDays >= 1) {
    return {
      period: 'days',
      count: diffDays,
    }
  }

  const diffHours = now.diff(d, 'hours')
  if (diffHours >= 1) {
    return {
      period: 'hours',
      count: diffHours,
    }
  }

  const diffMinutes = now.diff(d, 'minutes')
  if (diffMinutes >= 1) {
    return {
      period: 'minutes',
      count: diffMinutes,
    }
  }

  const diffSeconds = now.diff(d, 'seconds')
  return {
    period: 'seconds',
    count: diffSeconds,
  }
}
