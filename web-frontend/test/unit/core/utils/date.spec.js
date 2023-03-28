import {
  getDateInTimezone,
  getMonthlyTimestamps,
} from '@baserow/modules/core/utils/date'
import moment from '@baserow/modules/core/moment'

describe('getDateInTimezone', () => {
  test('in UTC', () => {
    const result = getDateInTimezone({
      year: 2022,
      month: 10,
      day: 17,
      timezone: 'utc',
    })

    expect(result.toISOString()).toBe('2022-11-17T00:00:00.000Z')
  })

  test('in a different timezone', () => {
    const result = getDateInTimezone({
      year: 2022,
      month: 10,
      day: 17,
      timezone: 'Asia/Kamchatka',
    })

    expect(result.toISOString()).toBe('2022-11-16T12:00:00.000Z')
  })
})

describe('getMonthlyTimestamps', () => {
  test('get valid timestamps for a date in UTC in march 2023', () => {
    const dateTime = moment.tz('2023-03-15T00:00:00', 'utc')

    const monthlyTimestamps = getMonthlyTimestamps(dateTime)
    const monthlyTimestampsFormatted = {
      firstDayNextMonth: monthlyTimestamps.firstDayNextMonth.toISOString(),
      firstDayPreviousMonth:
        monthlyTimestamps.firstDayPreviousMonth.toISOString(),
      fromTimestamp: monthlyTimestamps.fromTimestamp.toISOString(),
      toTimestamp: monthlyTimestamps.toTimestamp.toISOString(),
      firstMondayDayOfRange: monthlyTimestamps.firstMondayDayOfRange,
      visibleNumberOfDaysFromNextMonth:
        monthlyTimestamps.visibleNumberOfDaysFromNextMonth,
      visibleNumberOfDaysFromPreviousMonth:
        monthlyTimestamps.visibleNumberOfDaysFromPreviousMonth,
    }

    expect(monthlyTimestampsFormatted).toStrictEqual({
      firstDayNextMonth: '2023-04-01T00:00:00.000Z',
      firstDayPreviousMonth: '2023-02-01T00:00:00.000Z',
      fromTimestamp: '2023-02-27T00:00:00.000Z',
      toTimestamp: '2023-04-03T00:00:00.000Z',
      firstMondayDayOfRange: 27,
      visibleNumberOfDaysFromNextMonth: 2,
      visibleNumberOfDaysFromPreviousMonth: 2,
    })
  })

  test('get valid timestamps for a date in UTC in april 2023', () => {
    const dateTime = moment.tz('2023-04-22T00:00:00', 'utc')

    const monthlyTimestamps = getMonthlyTimestamps(dateTime)
    const monthlyTimestampsFormatted = {
      firstDayNextMonth: monthlyTimestamps.firstDayNextMonth.toISOString(),
      firstDayPreviousMonth:
        monthlyTimestamps.firstDayPreviousMonth.toISOString(),
      fromTimestamp: monthlyTimestamps.fromTimestamp.toISOString(),
      toTimestamp: monthlyTimestamps.toTimestamp.toISOString(),
      firstMondayDayOfRange: monthlyTimestamps.firstMondayDayOfRange,
      visibleNumberOfDaysFromNextMonth:
        monthlyTimestamps.visibleNumberOfDaysFromNextMonth,
      visibleNumberOfDaysFromPreviousMonth:
        monthlyTimestamps.visibleNumberOfDaysFromPreviousMonth,
    }

    expect(monthlyTimestampsFormatted).toStrictEqual({
      firstDayNextMonth: '2023-05-01T00:00:00.000Z',
      firstDayPreviousMonth: '2023-03-01T00:00:00.000Z',
      fromTimestamp: '2023-03-27T00:00:00.000Z',
      toTimestamp: '2023-05-01T00:00:00.000Z',
      firstMondayDayOfRange: 27,
      visibleNumberOfDaysFromNextMonth: 0,
      visibleNumberOfDaysFromPreviousMonth: 5,
    })
  })

  test('get valid timestamps for a date in UTC in may 2023', () => {
    const dateTime = moment.tz('2023-05-22T00:00:00', 'utc')

    const monthlyTimestamps = getMonthlyTimestamps(dateTime)
    const monthlyTimestampsFormatted = {
      firstDayNextMonth: monthlyTimestamps.firstDayNextMonth.toISOString(),
      firstDayPreviousMonth:
        monthlyTimestamps.firstDayPreviousMonth.toISOString(),
      fromTimestamp: monthlyTimestamps.fromTimestamp.toISOString(),
      toTimestamp: monthlyTimestamps.toTimestamp.toISOString(),
      firstMondayDayOfRange: monthlyTimestamps.firstMondayDayOfRange,
      visibleNumberOfDaysFromNextMonth:
        monthlyTimestamps.visibleNumberOfDaysFromNextMonth,
      visibleNumberOfDaysFromPreviousMonth:
        monthlyTimestamps.visibleNumberOfDaysFromPreviousMonth,
    }

    expect(monthlyTimestampsFormatted).toStrictEqual({
      firstDayNextMonth: '2023-06-01T00:00:00.000Z',
      firstDayPreviousMonth: '2023-04-01T00:00:00.000Z',
      fromTimestamp: '2023-05-01T00:00:00.000Z',
      toTimestamp: '2023-06-05T00:00:00.000Z',
      firstMondayDayOfRange: 1,
      visibleNumberOfDaysFromNextMonth: 4,
      visibleNumberOfDaysFromPreviousMonth: 0,
    })
  })
})
