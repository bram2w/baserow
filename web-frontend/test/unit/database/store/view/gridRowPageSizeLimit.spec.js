import gridStore from '@baserow/modules/database/store/view/grid'
import GridService from '@baserow/modules/database/services/view/grid'
import { TestApp } from '@baserow/test/helpers/testApp'

const view = {
  id: 1,
  type: 'grid',
  filter_type: 'AND',
  filters: [],
  filter_groups: [],
  filters_disabled: false,
  sortings: [],
  group_bys: [{ id: 1, view: 1, field: 1, order: 'ASC', type: 'default' }],
}

// Replies to the grid rows endpoint with one row per requested position, using the
// position as the row id, and records the requested ranges.
const mockGridRows = (mockServer, requests) => {
  mockServer.mock.onGet('/database/views/grid/1/').reply((config) => {
    const offset = Number(config.params.get('offset') || 0)
    const limit = Number(config.params.get('limit'))
    requests.push({ offset, limit, include: config.params.get('include') })
    const results = []
    const rowMetadata = {}
    for (let id = offset; id < offset + limit; id++) {
      results.push({ id, order: `${id}.00`, field_1: 'A' })
      rowMetadata[id] = { position: id }
    }
    return [
      200,
      {
        count: 1000,
        results,
        row_metadata: rowMetadata,
        ...(offset === 0 ? { field_options: { 1: { hidden: false } } } : {}),
      },
    ]
  })
}

describe('Grid view rows respect the row page size limit', () => {
  let testApp = null
  let mockServer = null
  let store = null
  let originalLimit = null

  beforeEach(() => {
    testApp = new TestApp()
    mockServer = testApp.mockServer
    store = testApp.createStore({ modules: { grid: gridStore } })
    originalLimit = store.$config.public.baserowRowPageSizeLimit
    store.$config.public.baserowRowPageSizeLimit = 200
  })

  afterEach(async () => {
    store.$config.public.baserowRowPageSizeLimit = originalLimit
    await testApp.afterEach()
  })

  test('fetchRowsInChunks splits a large limit and merges the responses', async () => {
    const requests = []
    mockGridRows(mockServer, requests)

    const { data } = await GridService(store.$client).fetchRowsInChunks({
      chunkSize: 200,
      gridId: 1,
      offset: 0,
      limit: 450,
      includeFieldOptions: true,
    })

    expect(requests.map(({ offset, limit }) => ({ offset, limit }))).toEqual([
      { offset: 0, limit: 200 },
      { offset: 200, limit: 200 },
      { offset: 400, limit: 50 },
    ])
    // Field options are only needed once.
    expect(requests.map(({ include }) => include)).toEqual([
      'field_options,row_metadata',
      'row_metadata',
      'row_metadata',
    ])
    expect(data.results.map((row) => row.id)).toEqual(
      Array.from({ length: 450 }, (_, index) => index)
    )
    expect(Object.keys(data.row_metadata)).toHaveLength(450)
    expect(data.count).toBe(1000)
    expect(data.field_options).toEqual({ 1: { hidden: false } })
  })

  test('fetchRowsInChunks makes a single request within the limit', async () => {
    const requests = []
    mockGridRows(mockServer, requests)

    const { data } = await GridService(store.$client).fetchRowsInChunks({
      chunkSize: 200,
      gridId: 1,
      offset: 10,
      limit: 200,
    })

    expect(requests).toHaveLength(1)
    expect(requests[0]).toMatchObject({ offset: 10, limit: 200 })
    expect(data.results).toHaveLength(200)
  })

  test('sections spanning a collapsed group are fetched in chunks', async () => {
    const requests = []
    mockGridRows(mockServer, requests)
    store.replaceState({
      ...store.state,
      grid: Object.assign(gridStore.state(), {
        activeGroupBys: [{ field: 1 }],
        count: 1000,
      }),
    })

    // Two visible groups with a large collapsed group in between, so the
    // visible rows are 600 positions apart in the absolute row space.
    const sections = [
      { absoluteRowOffset: 0, startPosition: 0, endPosition: 10 },
      { absoluteRowOffset: 600, startPosition: 0, endPosition: 10 },
    ]
    const data = await store.dispatch('grid/fetchGroupByRowsForSections', {
      gridId: 1,
      view,
      fields: [{ id: 1, type: 'text', name: 'Text' }],
      sections,
      layout: { items: [] },
    })

    expect(requests.length).toBeGreaterThan(1)
    for (const { limit } of requests) {
      expect(limit).toBeLessThanOrEqual(200)
    }
    // The merged rows still line up with their absolute position.
    expect(data.results[0].id).toBe(requests[0].offset)
    data.results.forEach((row, index) => {
      expect(row.id).toBe(requests[0].offset + index)
    })
    expect(data.results.at(-1).id).toBeGreaterThanOrEqual(609)
  })
})
