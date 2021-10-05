import { MultipleSelectFieldType } from '@baserow/modules/database/fieldTypes'
import { firstBy } from 'thenby'
import { TestApp } from '@baserow/test/helpers/testApp'

const testTableData = [
  {
    id: 1,
    order: '1.00000000000000000000',
    field_272: 'Tesla',
    field_275: [{ id: 146, value: 'C', color: 'red' }],
  },
  {
    id: 2,
    order: '2.00000000000000000000',
    field_272: 'Amazon',
    field_275: [{ id: 144, value: 'A', color: 'blue' }],
  },
  {
    id: 3,
    order: '3.00000000000000000000',
    field_272: '',
    field_275: [
      { id: 144, value: 'A', color: 'blue' },
      { id: 145, value: 'B', color: 'orange' },
    ],
  },
  {
    id: 4,
    order: '4.00000000000000000000',
    field_272: '',
    field_275: [
      { id: 144, value: 'A', color: 'blue' },
      { id: 145, value: 'B', color: 'orange' },
      { id: 146, value: 'C', color: 'red' },
    ],
  },
  {
    id: 5,
    order: '5.00000000000000000000',
    field_272: '',
    field_275: [
      { id: 149, value: 'F', color: 'light-gray' },
      { id: 148, value: 'E', color: 'dark-red' },
    ],
  },
  {
    id: 6,
    order: '6.00000000000000000000',
    field_272: '',
    field_275: [
      { id: 149, value: 'F', color: 'light-gray' },
      { id: 144, value: 'A', color: 'blue' },
    ],
  },
]

const testTableDataWithNull = [
  {
    id: 1,
    order: '1.00000000000000000000',
    field_272: 'Tesla',
    field_275: [],
  },
  {
    id: 2,
    order: '2.00000000000000000000',
    field_272: 'Amazon',
    field_275: [{ id: 144, value: 'A', color: 'blue' }],
  },
  {
    id: 3,
    order: '3.00000000000000000000',
    field_272: '',
    field_275: [
      { id: 144, value: 'A', color: 'blue' },
      { id: 145, value: 'B', color: 'orange' },
    ],
  },
]

describe('MultipleSelectFieldType sorting', () => {
  let testApp = null
  let multipleSelectFieldType = null
  let ASC = null
  let DESC = null
  let sortASC = firstBy()
  let sortDESC = firstBy()

  beforeAll(() => {
    testApp = new TestApp()
    multipleSelectFieldType = new MultipleSelectFieldType()
    ASC = multipleSelectFieldType.getSort('field_275', 'ASC')
    DESC = multipleSelectFieldType.getSort('field_275', 'DESC')
    sortASC = sortASC.thenBy(ASC)
    sortDESC = sortDESC.thenBy(DESC)
  })

  afterEach(() => {
    testApp.afterEach()
  })

  test('Test ascending and descending order', () => {
    testTableData.sort(sortASC)
    let ids = testTableData.map((obj) => obj.id)
    expect(ids).toEqual([2, 3, 4, 1, 6, 5])

    testTableData.sort(sortDESC)
    ids = testTableData.map((obj) => obj.id)
    expect(ids).toEqual([5, 6, 1, 4, 3, 2])
  })

  test('Test ascending and descending order with null values', () => {
    testTableDataWithNull.sort(sortASC)
    let ids = testTableDataWithNull.map((obj) => obj.id)
    expect(ids).toEqual([1, 2, 3])

    testTableDataWithNull.sort(sortDESC)
    ids = testTableDataWithNull.map((obj) => obj.id)
    expect(ids).toEqual([3, 2, 1])
  })
})
