import { createApplication } from '@baserow/test/fixtures/applications'
import { createGroup } from '@baserow/test/fixtures/groups'
import {
  createGridView,
  createPublicGridView,
} from '@baserow/test/fixtures/view'
import { createFields } from '@baserow/test/fixtures/fields'
import {
  createPublicGridViewRows,
  createGridRows,
} from '@baserow/test/fixtures/grid'
import {
  createGalleryRows,
  createGalleryView,
} from '@baserow/test/fixtures/gallery'

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

  loadPermissions(group, result = {}) {
    this.mock.onGet(`/groups/${group.id}/permissions/`).reply(200, result)
  }

  async createAppAndGroup(table) {
    const group = createGroup(this.mock, {})
    this.loadPermissions(group)
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

  createGridView(
    application,
    table,
    { filters = [], sortings = [], decorations = [], ...rest }
  ) {
    return createGridView(this.mock, application, table, {
      filters,
      sortings,
      decorations,
      ...rest,
    })
  }

  createPublicGridView(viewSlug, { name, fields = [], sortings = [] }) {
    return createPublicGridView(this.mock, viewSlug, { name, fields, sortings })
  }

  createPublicGridViewRows(viewSlug, fields, rows) {
    return createPublicGridViewRows(this.mock, viewSlug, fields, rows)
  }

  createGalleryView(
    application,
    table,
    { filters = [], sortings = [], decorations = [], ...rest }
  ) {
    return createGalleryView(this.mock, application, table, {
      filters,
      sortings,
      decorations,
      ...rest,
    })
  }

  createFields(application, table, fields) {
    return createFields(this.mock, application, table, fields)
  }

  createGridRows(gridView, fields, rows) {
    return createGridRows(this.mock, gridView, fields, rows)
  }

  createGalleryRows(gridView, fields, rows) {
    return createGalleryRows(this.mock, gridView, fields, rows)
  }

  nextSearchForTermWillReturn(searchTerm, gridView, results) {
    this.mock
      .onGet(`/database/views/grid/${gridView.id}/`, {
        params: {
          asymmetricMatch(actual) {
            return (
              actual.get('count') === 'true' &&
              actual.get('search') === searchTerm
            )
          },
        },
      })
      .reply(200, {
        count: results.length,
      })

    this.mock
      .onGet(`/database/views/grid/${gridView.id}/`, {
        params: {
          asymmetricMatch(actual) {
            return (
              actual.get('limit') === '120' &&
              actual.get('offset') === '0' &&
              actual.get('search') === searchTerm &&
              actual.get('include') === 'row_metadata'
            )
          },
        },
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

  updateViewFilter(filterId, newValue) {
    this.mock
      .onPatch(`/database/views/filter/${filterId}/`, { value: newValue })
      .reply(200)
  }

  updateFieldOptions(viewId, values) {
    this.mock
      .onPatch(`/database/views/${viewId}/field-options/`, {
        field_options: values,
      })
      .replyOnce(200)
  }

  // Grid view aggregation data mocks
  getFieldAggregationData(viewId, fieldId, rawType, result, error = false) {
    const mock = this.mock.onGet(
      `/database/views/grid/${viewId}/aggregation/${fieldId}/`,
      {
        params: {
          asymmetricMatch(actual) {
            return actual.get('type') === rawType
          },
        },
      }
    )
    if (error) {
      mock.replyOnce(500)
    } else {
      mock.replyOnce(200, result)
    }
  }

  getAllFieldAggregationData(viewId, result, error = false) {
    const mock = this.mock.onGet(`/database/views/grid/${viewId}/aggregations/`)
    if (error) {
      mock.replyOnce(500)
    } else {
      mock.replyOnce(200, result)
    }
  }

  createDecoration(view, values, result) {
    this.mock
      .onPost(`/database/views/${view.id}/decorations/`, values)
      .replyOnce(200, result)
  }

  updateDecoration(decoration, values, result) {
    this.mock
      .onPatch(`/database/views/decoration/${decoration.id}/`, values)
      .replyOnce(200, result)
  }

  deleteDecoration(decoration) {
    this.mock
      .onDelete(`/database/views/decoration/${decoration.id}/`)
      .replyOnce(200)
  }

  resetMockEndpoints() {
    this.mock.reset()
  }
}
