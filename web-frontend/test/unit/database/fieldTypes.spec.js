import { TestApp } from '@baserow/test/helpers/testApp'

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
    primary: true,
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
}

const valuesToCall = [null, undefined]

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
          value.prepareValueForCopy(fieldItem, valueType)
        }
        expect(t).not.toThrow(TypeError)
      }
    }
  )
})
