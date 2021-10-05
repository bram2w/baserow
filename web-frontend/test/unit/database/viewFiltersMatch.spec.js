import { TestApp } from '@baserow/test/helpers/testApp'
import moment from '@baserow/modules/core/moment'
import {
  DateBeforeViewFilterType,
  DateAfterViewFilterType,
  DateEqualViewFilterType,
  DateNotEqualViewFilterType,
  DateEqualsTodayViewFilterType,
  MultipleSelectHasFilterType,
  MultipleSelectHasNotFilterType,
  HasFileTypeViewFilterType,
} from '@baserow/modules/database/viewFilters'

const dateBeforeCasesWithTimezone = [
  {
    rowValue: '2021-08-10T21:59:37.940086Z',
    filterValue: '2021-08-11',
    timezone: 'Europe/Berlin',
    expected: true,
  },
  {
    rowValue: '2021-08-10',
    filterValue: '2021-08-11',
    timezone: 'Europe/Berlin',
    expected: true,
  },
  {
    rowValue: '2021-08-11',
    filterValue: '2021-08-11',
    timezone: 'Europe/Berlin',
    expected: false,
  },
  {
    rowValue: '2021-08-10T22:59:37.940086Z',
    filterValue: '2021-08-11',
    timezone: 'Europe/London',
    expected: true,
  },
  {
    rowValue: '2021-08-10T22:01:37.940086Z',
    filterValue: '2021-08-11',
    timezone: 'Europe/Berlin',
    expected: false,
  },
  {
    rowValue: '2021-08-10T23:01:37.940086Z',
    filterValue: '2021-08-11',
    timezone: 'Europe/London',
    expected: false,
  },
]

const dateBeforeCasesWithoutTimezone = [
  {
    rowValue: '2021-08-10T23:59:37.940086Z',
    filterValue: '2021-08-11',
    expected: true,
  },
  {
    rowValue: '2021-08-10',
    filterValue: '2021-08-11',
    expected: true,
  },
  {
    rowValue: '2021-08-11T00:01:37.940086Z',
    filterValue: '2021-08-11',
    expected: false,
  },
  {
    rowValue: '2021-08-11',
    filterValue: '2021-08-11',
    expected: false,
  },
]

const dateAfterCasesWithTimezone = [
  {
    rowValue: '2021-08-11T22:01:37.940086Z',
    filterValue: '2021-08-11',
    timezone: 'Europe/Berlin',
    expected: true,
  },
  {
    rowValue: '2021-08-12',
    filterValue: '2021-08-11',
    timezone: 'Europe/Berlin',
    expected: true,
  },
  {
    rowValue: '2021-08-10',
    filterValue: '2021-08-11',
    timezone: 'Europe/Berlin',
    expected: false,
  },
  {
    rowValue: '2021-08-11T23:01:37.940086Z',
    filterValue: '2021-08-11',
    timezone: 'Europe/London',
    expected: true,
  },
  {
    rowValue: '2021-08-11T21:59:37.940086Z',
    filterValue: '2021-08-11',
    timezone: 'Europe/Berlin',
    expected: false,
  },
  {
    rowValue: '2021-08-11T22:59:37.940086Z',
    filterValue: '2021-08-11',
    timezone: 'Europe/London',
    expected: false,
  },
]

const dateAfterCasesWithoutTimezone = [
  {
    rowValue: '2021-08-12T00:01:37.940086Z',
    filterValue: '2021-08-11',
    expected: true,
  },
  {
    rowValue: '2021-08-12',
    filterValue: '2021-08-11',
    expected: true,
  },
  {
    rowValue: '2021-08-11T23:59:37.940086Z',
    filterValue: '2021-08-11',
    expected: false,
  },
  {
    rowValue: '2021-08-11',
    filterValue: '2021-08-11',
    expected: false,
  },
]

const dateEqualCasesWithTimezone = [
  {
    rowValue: '2021-08-11T21:59:37.940086Z',
    filterValue: '2021-08-11',
    timezone: 'Europe/Berlin',
    expected: true,
  },
  {
    rowValue: '2021-08-11',
    filterValue: '2021-08-11',
    timezone: 'Europe/Berlin',
    expected: true,
  },
  {
    rowValue: '2021-08-11T22:59:37.940086Z',
    filterValue: '2021-08-11',
    timezone: 'Europe/London',
    expected: true,
  },
  {
    rowValue: '2021-08-10T22:01:37.940086Z',
    filterValue: '2021-08-11',
    timezone: 'Europe/Berlin',
    expected: true,
  },
  {
    rowValue: '2021-08-10T23:01:37.940086Z',
    filterValue: '2021-08-11',
    timezone: 'Europe/London',
    expected: true,
  },
  {
    rowValue: '2021-08-10T21:59:37.940086Z',
    filterValue: '2021-08-11',
    timezone: 'Europe/Berlin',
    expected: false,
  },
  {
    rowValue: '2021-08-10T22:59:37.940086Z',
    filterValue: '2021-08-11',
    timezone: 'Europe/London',
    expected: false,
  },
]

const dateEqualWithoutTimezone = [
  {
    rowValue: '2021-08-11T23:59:37.940086Z',
    filterValue: '2021-08-11',
    expected: true,
  },
  {
    rowValue: '2021-08-11',
    filterValue: '2021-08-11',
    expected: true,
  },
  {
    rowValue: '2021-08-11T00:01:37.940086Z',
    filterValue: '2021-08-11',
    expected: true,
  },
  {
    rowValue: '2021-08-12T00:01:37.940086Z',
    filterValue: '2021-08-11',
    expected: false,
  },
  {
    rowValue: '2021-08-12',
    filterValue: '2021-08-11',
    expected: false,
  },
]

const dateNotEqualCasesWithTimezone = [
  {
    rowValue: '2021-08-11T22:30:37.940086Z',
    filterValue: '2021-08-11',
    timezone: 'Europe/Berlin',
    expected: true,
  },
  {
    rowValue: '2021-08-12',
    filterValue: '2021-08-11',
    timezone: 'Europe/Berlin',
    expected: true,
  },
  {
    rowValue: '2021-08-11',
    filterValue: '2021-08-11',
    timezone: 'Europe/Berlin',
    expected: false,
  },
  {
    rowValue: '2021-08-11T23:30:37.940086Z',
    filterValue: '2021-08-11',
    timezone: 'Europe/London',
    expected: true,
  },
  {
    rowValue: '2021-08-10T22:01:37.940086Z',
    filterValue: '2021-08-11',
    timezone: 'Europe/Berlin',
    expected: false,
  },
  {
    rowValue: '2021-08-10T23:01:37.940086Z',
    filterValue: '2021-08-11',
    timezone: 'Europe/London',
    expected: false,
  },
]

const dateNotEqualCasesWithoutTimezone = [
  {
    rowValue: '2021-08-11T23:59:37.940086Z',
    filterValue: '2021-08-12',
    expected: true,
  },
  {
    rowValue: '2021-08-13T00:01:37.940086Z',
    filterValue: '2021-08-12',
    expected: true,
  },
  {
    rowValue: '2021-08-10',
    filterValue: '2021-08-11',
    expected: true,
  },
  {
    rowValue: '2021-08-12',
    filterValue: '2021-08-11',
    expected: true,
  },
  {
    rowValue: '2021-08-11T22:59:37.940086Z',
    filterValue: '2021-08-11',
    expected: false,
  },
  {
    rowValue: '2021-08-11',
    filterValue: '2021-08-11',
    expected: false,
  },
]

const dateToday = [
  {
    rowValue: moment().utc().format(),
    filterValue: 'Europe/Berlin',
    expected: true,
  },
  {
    rowValue: '1970-08-11T23:30:37.940086Z',
    filterValue: 'Europe/Berlin',
    expected: false,
  },
]

const multipleSelectValuesHas = [
  {
    rowValue: [
      { id: 155, value: 'A', color: 'green' },
      { id: 154, value: 'B', color: 'green' },
    ],
    filterValue: 154,
    expected: true,
  },
  {
    rowValue: [
      { id: 155, value: 'A', color: 'green' },
      { id: 154, value: 'B', color: 'green' },
    ],
    filterValue: 200,
    expected: false,
  },
  {
    rowValue: [
      { id: 155, value: 'A', color: 'green' },
      { id: 154, value: 'B', color: 'green' },
    ],
    filterValue: 'wrong_type',
    expected: true,
  },
]

const multipleSelectValuesHasNot = [
  {
    rowValue: [
      { id: 155, value: 'A', color: 'green' },
      { id: 154, value: 'B', color: 'green' },
    ],
    filterValue: 154,
    expected: false,
  },
  {
    rowValue: [
      { id: 155, value: 'A', color: 'green' },
      { id: 154, value: 'B', color: 'green' },
    ],
    filterValue: 200,
    expected: true,
  },
  {
    rowValue: [
      { id: 155, value: 'A', color: 'green' },
      { id: 154, value: 'B', color: 'green' },
    ],
    filterValue: 'wrong_type',
    expected: true,
  },
]

describe('All Tests', () => {
  let testApp = null

  beforeAll(() => {
    testApp = new TestApp()
  })

  afterEach(() => {
    testApp.afterEach()
  })

  test.each(dateBeforeCasesWithTimezone)(
    'BeforeViewFilter with Timezone',
    (values) => {
      const result = new DateBeforeViewFilterType({ app: testApp }).matches(
        values.rowValue,
        values.filterValue,
        { timezone: values.timezone }
      )
      expect(result).toBe(values.expected)
    }
  )

  test.each(dateBeforeCasesWithoutTimezone)(
    'BeforeViewFilter without Timezone',
    (values) => {
      const result = new DateBeforeViewFilterType({ app: testApp }).matches(
        values.rowValue,
        values.filterValue,
        {}
      )
      expect(result).toBe(values.expected)
    }
  )

  test.each(dateAfterCasesWithTimezone)(
    'AfterViewFilter with Timezone',
    (values) => {
      const result = new DateAfterViewFilterType({ app: testApp }).matches(
        values.rowValue,
        values.filterValue,
        { timezone: values.timezone }
      )
      expect(result).toBe(values.expected)
    }
  )

  test.each(dateAfterCasesWithoutTimezone)(
    'AfterViewFilter without Timezone',
    (values) => {
      const result = new DateAfterViewFilterType({ app: testApp }).matches(
        values.rowValue,
        values.filterValue,
        {}
      )
      expect(result).toBe(values.expected)
    }
  )

  test.each(dateEqualCasesWithTimezone)('DateEqual with Timezone', (values) => {
    const result = new DateEqualViewFilterType({ app: testApp }).matches(
      values.rowValue,
      values.filterValue,
      { timezone: values.timezone }
    )
    expect(result).toBe(values.expected)
  })

  test.each(dateEqualWithoutTimezone)(
    'DateEqual without Timezone',
    (values) => {
      const result = new DateEqualViewFilterType({ app: testApp }).matches(
        values.rowValue,
        values.filterValue,
        { timezone: values.timezone }
      )
      expect(result).toBe(values.expected)
    }
  )
  test.each(dateNotEqualCasesWithTimezone)(
    'DateNotEqual with Timezone',
    (values) => {
      const result = new DateNotEqualViewFilterType({ app: testApp }).matches(
        values.rowValue,
        values.filterValue,
        { timezone: values.timezone }
      )
      expect(result).toBe(values.expected)
    }
  )
  test.each(dateNotEqualCasesWithoutTimezone)(
    'DateNotEqual without Timezone',
    (values) => {
      const result = new DateNotEqualViewFilterType({ app: testApp }).matches(
        values.rowValue,
        values.filterValue,
        {}
      )
      expect(result).toBe(values.expected)
    }
  )

  test.each(dateToday)('DateToday', (values) => {
    const result = new DateEqualsTodayViewFilterType({ app: testApp }).matches(
      values.rowValue,
      values.filterValue,
      {}
    )
    expect(result).toBe(values.expected)
  })

  test.each(multipleSelectValuesHas)('MultipleSelect Has', (values) => {
    const result = new MultipleSelectHasFilterType().matches(
      values.rowValue,
      values.filterValue,
      {}
    )
    expect(result).toBe(values.expected)
  })

  test.each(multipleSelectValuesHasNot)('MultipleSelect Has Not', (values) => {
    const result = new MultipleSelectHasNotFilterType().matches(
      values.rowValue,
      values.filterValue,
      {}
    )
    expect(result).toBe(values.expected)
  })

  test('HasFileType contains image', () => {
    expect(new HasFileTypeViewFilterType().matches([], '', {})).toBe(true)
    expect(new HasFileTypeViewFilterType().matches([], 'image', {})).toBe(false)
    expect(new HasFileTypeViewFilterType().matches([], 'document', {})).toBe(
      false
    )
    expect(
      new HasFileTypeViewFilterType().matches([{ is_image: true }], 'image', {})
    ).toBe(true)
    expect(
      new HasFileTypeViewFilterType().matches(
        [{ is_image: true }],
        'document',
        {}
      )
    ).toBe(false)
    expect(
      new HasFileTypeViewFilterType().matches(
        [{ is_image: false }],
        'image',
        {}
      )
    ).toBe(false)
    expect(
      new HasFileTypeViewFilterType().matches(
        [{ is_image: false }],
        'document',
        {}
      )
    ).toBe(true)
    expect(
      new HasFileTypeViewFilterType().matches(
        [{ is_image: true }, { is_image: false }],
        'image',
        {}
      )
    ).toBe(true)
    expect(
      new HasFileTypeViewFilterType().matches(
        [{ is_image: true }, { is_image: false }],
        'document',
        {}
      )
    ).toBe(true)
  })
})
