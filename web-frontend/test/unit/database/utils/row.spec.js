import { prepareRowForRequest } from '@baserow/modules/database/utils/row'
import { TestApp } from '@baserow/test/helpers/testApp'

describe('Row untilities', () => {
  describe('prepareRowForRequest', () => {
    let testApp = null
    let store = null

    beforeAll(() => {
      testApp = new TestApp()
      store = testApp.store
    })

    afterEach((done) => {
      testApp.afterEach().then(done)
    })

    const rowsToTest = [
      // Empty case
      {
        input: {
          row: {},
          fields: [],
        },
        output: {},
      },
      // Basic case of just a simple text field
      {
        input: {
          row: {
            field_1: 'value',
          },
          fields: [
            {
              name: 'field_1',
              id: 1,
              _: {
                type: {
                  type: 'text',
                },
              },
            },
          ],
        },
        output: {
          field_1: 'value',
        },
      },
      // Empty value is being used if no value is provided
      {
        input: {
          row: {
            field_1: 'value',
          },
          fields: [
            {
              name: 'field_1',
              id: 1,
              _: {
                type: {
                  type: 'text',
                },
              },
            },
            {
              name: 'field_2',
              id: 2,
              text_default: 'some default',
              _: {
                type: {
                  type: 'text',
                },
              },
            },
          ],
        },
        output: {
          field_1: 'value',
          field_2: 'some default',
        },
      },
      // Read only field
      {
        input: {
          row: {
            field_1: 'value',
          },
          fields: [
            {
              name: 'field_1',
              id: 1,
              _: {
                type: {
                  type: 'formula',
                },
              },
            },
          ],
        },
        output: {},
      },
      // Missing value
      {
        input: {
          row: {},
          fields: [
            {
              name: 'field_1',
              id: 1,
              text_default: 'some default',
              _: {
                type: {
                  type: 'text',
                },
              },
            },
          ],
        },
        output: {
          field_1: 'some default',
        },
      },
    ]

    test.each(rowsToTest)(
      'Test that %o is correctly prepared for request',
      ({ input, output }) => {
        expect(
          prepareRowForRequest(input.row, input.fields, store.$registry)
        ).toEqual(output)
      },
      200
    )
  })
})
