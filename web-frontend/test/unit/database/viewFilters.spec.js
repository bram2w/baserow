import { TestApp } from '@baserow/test/helpers/testApp'
import { createFile } from '@baserow/test/fixtures/fields'
import {
  EqualViewFilterType,
  FilenameContainsViewFilterType,
} from '@baserow/modules/database/viewFilters'

describe('View Filter Tests', () => {
  let testApp = null
  let mockServer = null
  let store = null

  beforeAll(() => {
    testApp = new TestApp()
    mockServer = testApp.mockServer
    store = testApp.store
  })

  afterEach(() => {
    testApp.afterEach()
  })

  test('When An Equals Filter is applied a string field correctly indicates if the row will continue to match after an edit', async () => {
    await thereIsATableWithRowAndFilter(
      {
        name: 'Text Field Field',
        type: 'text',
        primary: true,
      },
      { id: 1, order: 0, field_1: 'exactly_matching_string' },
      {
        id: 1,
        view: 1,
        field: 1,
        type: EqualViewFilterType.getType(),
        value: 'exactly_matching_string',
      }
    )

    const row = store.getters['page/view/grid/getRow'](1)

    await editFieldWithoutSavingNewValue(row, 'exactly_matching_string')
    expect(row._.matchFilters).toBe(true)

    await editFieldWithoutSavingNewValue(row, 'newly_edited_value_not_matching')
    expect(row._.matchFilters).toBe(false)
  })

  async function thereIsATableWithRowAndFilter(field, row, filter) {
    const table = mockServer.createTable()
    const { application } = await mockServer.createAppAndGroup(table)
    const gridView = mockServer.createGridView(application, table, [filter])
    const fields = mockServer.createFields(application, table, [field])

    mockServer.createRows(gridView, fields, [row])
    await store.dispatch('page/view/grid/fetchInitial', {
      gridId: 1,
      fields: [field],
      primary: {},
    })
    await store.dispatch('view/fetchAll', { id: 1 })
  }

  test('When An Filename Contains Filter is applied a file field correctly indicates if the row will continue to match after an edit', async () => {
    await thereIsATableWithRowAndFilter(
      {
        name: 'File Field',
        type: 'file',
        primary: true,
      },
      { id: 1, order: 0, field_1: [createFile('test_file_name')] },
      {
        id: 1,
        view: 1,
        field: 1,
        type: FilenameContainsViewFilterType.getType(),
        value: 'test_file_name',
      }
    )

    const row = store.getters['page/view/grid/getRow'](1)

    await editFieldWithoutSavingNewValue(row, [createFile('test_file_name')])
    expect(row._.matchFilters).toBe(true)

    await editFieldWithoutSavingNewValue(row, [
      createFile('not_matching_new_file_name'),
    ])
    expect(row._.matchFilters).toBe(false)

    await editFieldWithoutSavingNewValue(row, [
      createFile('test_file_name'),
      createFile('not_matching_new_file_name'),
    ])
    expect(row._.matchFilters).toBe(true)
  })

  async function editFieldWithoutSavingNewValue(row, newValue) {
    await store.dispatch('page/view/grid/updateMatchFilters', {
      view: store.getters['view/first'],
      fields: [],
      primary: {
        id: 1,
        type: 'file',
        primary: true,
      },
      row,
      overrides: {
        field_1: newValue,
      },
    })
  }
})
