import { getPrefills } from '@baserow/modules/database/utils/form'

const valuesToCall = [
  {
    query: {},
    result: {},
  },
  {
    query: { someUnrelatedQuery: 'someValue' },
    result: {},
  },
  {
    query: { prefill_value: 'value' },
    result: { value: 'value' },
  },
  {
    query: { 'prefill_value+with+spaces': 'value' },
    result: { 'value with spaces': 'value' },
  },
]

describe('Form utils test', () => {
  test.each(valuesToCall)(
    'Test that all values are correctly extracted from the query',
    ({ query, result }) => {
      expect(getPrefills(query)).toEqual(result)
    }
  )
})
