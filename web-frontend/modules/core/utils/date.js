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
  return {
    period: 'days',
    count: diffDays,
  }
}
