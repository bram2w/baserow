import { createApplication } from '@baserow/test/fixtures/applications'
import { createGroup } from '@baserow/test/fixtures/groups'
import { createGridView } from '@baserow/test/fixtures/view'
import { createFields } from '@baserow/test/fixtures/fields'
import { createRows } from '@baserow/test/fixtures/grid'

/**
 * MockServer is responsible for being the single place where we mock out calls to the
 * baserow server API in tests. This way when an API change is made we should only
 * need to make one change in this class to reflect the change in the tests.
 */
export class MockServer {
  constructor(mock, store) {
    this.mock = mock
    this.store = store
  }

  async createAppAndGroup(table) {
    const group = createGroup(this.mock, {})
    const application = createApplication(this.mock, {
      groupId: group.id,
      tables: [table],
    })
    await this.store.dispatch('group/fetchAll')
    await this.store.dispatch('application/fetchAll')
    return { application, group }
  }

  createTable() {
    return { id: 1, name: 'Test Table 1' }
  }

  createGridView(application, table, filters = []) {
    return createGridView(this.mock, application, table, {
      filters,
    })
  }

  createFields(application, table, fields) {
    return createFields(this.mock, application, table, fields)
  }

  createRows(gridView, fields, rows) {
    return createRows(this.mock, gridView, fields, rows)
  }

  nextSearchForTermWillReturn(searchTerm, gridView, results) {
    this.mock
      .onGet(`/database/views/grid/${gridView.id}/`, {
        params: { count: true, search: searchTerm },
      })
      .reply(200, {
        count: results.length,
      })

    this.mock
      .onGet(`/database/views/grid/${gridView.id}/`, {
        params: { limit: 120, offset: 0, search: searchTerm },
      })
      .reply(200, {
        count: results.length,
        next: null,
        previous: null,
        results,
      })
  }

  creatingRowInTableReturns(table, result) {
    this.mock.onPost(`/database/rows/table/${table.id}/`).reply(200, result)
  }

  resetMockEndpoints() {
    this.mock.reset()
  }
}
