import { TestApp } from '@baserow/test/helpers/testApp'
import { DateFieldType } from '@baserow/modules/database/fieldTypes'

const mockedFields = {
  text: {
    id: 1,
    name: 'text',
    order: 1,
    primary: true,
    table_id: 42,
    type: 'text',
  },
  long_text: {
    id: 2,
    name: 'long_text',
    order: 2,
    primary: false,
    table_id: 42,
    type: 'long_text',
  },
  link_row: {
    id: 3,
    name: 'link_row',
    order: 3,
    primary: false,
    table_id: 42,
    type: 'link_row',
    link_row_related_field: 270,
    link_row_table: 43,
  },
  number: {
    id: 4,
    name: 'number',
    order: 4,
    primary: false,
    table_id: 42,
    type: 'number',
    number_decimal_places: 1,
    number_negative: false,
    number_type: 'INTEGER',
  },
  rating: {
    id: 16,
    name: 'rating',
    order: 4,
    primary: false,
    table_id: 42,
    type: 'rating',
  },
  boolean: {
    id: 5,
    name: 'boolean',
    order: 5,
    primary: false,
    table_id: 42,
    type: 'boolean',
  },
  date: {
    id: 6,
    name: 'date',
    order: 6,
    primary: false,
    table_id: 42,
    type: 'date',
    date_format: 'EU',
    date_include_time: false,
    date_time_format: '24',
  },
  last_modified: {
    id: 7,
    name: 'last_modified',
    order: 7,
    primary: false,
    table_id: 42,
    type: 'last_modified',
    date_format: 'EU',
    date_include_time: false,
    date_time_format: '24',
  },
  created_on: {
    id: 8,
    name: 'created_on',
    order: 8,
    primary: false,
    table_id: 42,
    type: 'created_on',
    date_format: 'EU',
    date_include_time: false,
    date_time_format: '24',
  },
  url: {
    id: 9,
    name: 'url',
    order: 9,
    primary: false,
    table_id: 42,
    type: 'url',
  },
  email: {
    id: 10,
    name: 'email',
    order: 10,
    primary: false,
    table_id: 42,
    type: 'email',
  },
  file: {
    id: 11,
    name: 'file',
    order: 11,
    primary: false,
    table_id: 42,
    type: 'file',
  },
  single_select: {
    id: 12,
    name: 'single_select',
    order: 12,
    primary: false,
    table_id: 42,
    type: 'single_select',
    select_options: [],
  },
  phone_number: {
    id: 13,
    name: 'phone_number',
    order: 13,
    primary: false,
    table_id: 42,
    type: 'phone_number',
  },
  multiple_select: {
    id: 14,
    name: 'multiple_select',
    order: 14,
    primary: false,
    table_id: 42,
    type: 'multiple_select',
    select_options: [],
  },
  formula: {
    id: 15,
    name: 'formula',
    order: 16,
    primary: false,
    table_id: 42,
    type: 'formula',
  },
  lookup: {
    id: 16,
    name: 'lookup',
    order: 16,
    primary: false,
    table_id: 42,
    type: 'lookup',
  },
}

const valuesToCall = [null, undefined]

const datePrepareValueForCopy = [
  {
    fieldValue: '2021-12-04T10:57:22.184611Z',
    field: {
      date_format: 'EU',
      date_include_time: true,
      date_time_format: '24',
    },
    expectedValue: '04/12/2021 10:57',
  },
  {
    fieldValue: '2021-12-07T00:00:00',
    field: {
      date_format: 'US',
      date_include_time: false,
    },
    expectedValue: '12/07/2021',
  },
  {
    fieldValue: '2021-12-08T16:06:38.684274Z',
    field: {
      date_format: 'ISO',
      date_include_time: true,
      date_time_format: '12',
    },
    expectedValue: '2021-12-08 04:06 PM',
  },
]

const datePrepareValueForPaste = [
  // Date field with EU format
  {
    fieldValue: '04/12/2021',
    field: {
      date_format: 'EU',
    },
    expectedValue: '2021-12-04',
  },
  {
    fieldValue: '04/12/2021 22:57',
    field: {
      date_format: 'EU',
      date_include_time: true,
    },
    expectedValue: '2021-12-04T22:57:00Z',
  },
  {
    fieldValue: '04/12/2021 10:57 PM',
    field: {
      date_format: 'EU',
      date_include_time: true,
    },
    expectedValue: '2021-12-04T22:57:00Z',
  },
  {
    fieldValue: '2021-12-04',
    field: {
      date_format: 'EU',
    },
    expectedValue: '2021-12-04',
  },
  {
    fieldValue: '2021-12-04 22:57',
    field: {
      date_format: 'EU',
      date_include_time: true,
    },
    expectedValue: '2021-12-04T22:57:00Z',
  },
  {
    fieldValue: '2021-12-04 10:57 PM',
    field: {
      date_format: 'EU',
      date_include_time: true,
    },
    expectedValue: '2021-12-04T22:57:00Z',
  },
  {
    fieldValue: '2021-12-04T22:57:00Z',
    field: {
      date_format: 'EU',
      date_include_time: true,
    },
    expectedValue: '2021-12-04T22:57:00Z',
  },
  {
    fieldValue: '04/16/2021', // Explicit US date in EU field
    field: {
      date_format: 'EU',
    },
    expectedValue: '2021-04-16',
  },

  // Date field with US format
  {
    fieldValue: '04/12/2021',
    field: {
      date_format: 'US',
    },
    expectedValue: '2021-04-12',
  },
  {
    fieldValue: '04/12/2021 22:57',
    field: {
      date_format: 'US',
      date_include_time: true,
    },
    expectedValue: '2021-04-12T22:57:00Z',
  },
  {
    fieldValue: '04/12/2021 10:57 PM',
    field: {
      date_format: 'US',
      date_include_time: true,
    },
    expectedValue: '2021-04-12T22:57:00Z',
  },
]

describe('FieldType tests', () => {
  let testApp = null
  let fieldRegistry = null

  beforeAll(() => {
    testApp = new TestApp()
    fieldRegistry = testApp._app.$registry.registry.field

    // Make sure that we have a mockedField for every field type in the registry
    expect(Object.keys(fieldRegistry).sort()).toEqual(
      Object.keys(mockedFields).sort()
    )
  })

  afterEach(() => {
    testApp.afterEach()
  })
  test.each(valuesToCall)(
    'Verify that calling prepareValueForCopy will not throw when value is %s',
    (valueType) => {
      const fields = Object.entries(fieldRegistry)
      for (const [key, value] of fields) {
        const fieldItem = mockedFields[key]
        const t = () => {
          value.prepareValueForCopy(
            fieldItem,
            valueType,
            testApp.store.$registry
          )
        }
        expect(t).not.toThrow(TypeError)
      }
    }
  )

  test.each(datePrepareValueForCopy)(
    'Verify that prepareValueForCopy for DateFieldType returns the expected output',
    (value) => {
      const result = new DateFieldType().prepareValueForCopy(
        value.field,
        value.fieldValue
      )
      expect(result).toBe(value.expectedValue)
    }
  )

  test.each(datePrepareValueForPaste)(
    'Verify that prepareValueForPaste for DateFieldType returns the expected output',
    (value) => {
      const clipboardData = {
        getData() {
          return value.fieldValue
        },
      }

      const result = new DateFieldType().prepareValueForPaste(
        value.field,
        clipboardData
      )
      expect(result).toBe(value.expectedValue)
    }
  )
})
