import { TestApp } from '@baserow/test/helpers/testApp'
describe('Formula Functions Test', () => {
  let testApp = null
  beforeAll(() => {
    testApp = new TestApp()
  })

  afterEach(() => testApp.afterEach())
  test('All backend functions are in the frontend', () => {
    // Run baserow.contrib.database.field.test_formula_field_type.
    // test_all_functions_are_registered
    // to get a print out of all backend functions to update this variable.
    const backendFunctionTypeNames = [
      'upper',
      'lower',
      'concat',
      'totext',
      't',
      'replace',
      'search',
      'length',
      'reverse',
      'contains',
      'left',
      'right',
      'round',
      'even',
      'odd',
      'floor',
      'ceil',
      'abs',
      'power',
      'sqrt',
      'log',
      'ln',
      'exp',
      'sign',
      'mod',
      'trim',
      'trunc',
      'regex_replace',
      'multiply',
      'divide',
      'tonumber',
      'greatest',
      'least',
      'if',
      'equal',
      'isblank',
      'not',
      'not_equal',
      'greater_than',
      'greater_than_or_equal',
      'less_than',
      'less_than_or_equal',
      'and',
      'or',
      'datetime_format',
      'day',
      'month',
      'year',
      'second',
      'todate',
      'date_diff',
      'date_interval',
      'add',
      'minus',
      'row_id',
      'when_empty',
      'any',
      'every',
      'max',
      'min',
      'count',
      'filter',
      'join',
      'stddev_pop',
      'stddev_sample',
      'variance_sample',
      'variance_pop',
      'avg',
      'sum',
      'link',
      'button',
      'get_link_label',
      'get_link_url',
    ]
    const frontendFunctionTypes = Object.keys(
      testApp.store.$registry.getAll('formula_function')
    ).filter((f) => {
      return !['field', 'lookup'].includes(f)
    })

    expect(frontendFunctionTypes.sort()).toStrictEqual(
      backendFunctionTypeNames.sort()
    )
  })
})
