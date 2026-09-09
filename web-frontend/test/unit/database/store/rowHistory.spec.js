import { TestApp } from '@baserow/test/helpers/testApp'

describe('row history recovery', () => {
  let testApp
  let store
  const scope = { tableId: 1, rowId: 2 }
  const url = '/database/rows/table/1/2/history/'

  beforeEach(() => {
    testApp = new TestApp()
    store = testApp.store
  })

  afterEach(async () => {
    await testApp.afterEach()
  })

  test('repeated live entries replace rather than duplicate or inflate counts', async () => {
    testApp.mock.onGet(url).reply(200, { results: [{ id: 10 }], count: 1 })
    await store.dispatch('rowHistory/fetchInitial', scope)
    for (let i = 0; i < 2; i++) {
      await store.dispatch('rowHistory/forceCreate', {
        ...scope,
        rowHistoryEntry: { id: 10, after: { value: 'updated' } },
      })
    }
    expect(store.state.rowHistory.entries).toEqual([
      { id: 10, after: { value: 'updated' } },
    ])
    expect(store.getters['rowHistory/getTotalCount']).toBe(1)
  })

  test('initial fetch preserves and deduplicates live entries received in flight', async () => {
    let respond
    testApp.mock.onGet(url).reply(
      () =>
        new Promise((resolve) => {
          respond = resolve
        })
    )
    const pending = store.dispatch('rowHistory/fetchInitial', scope)
    await vi.waitFor(() => expect(respond).toBeTypeOf('function'))
    await store.dispatch('rowHistory/forceCreate', {
      ...scope,
      rowHistoryEntry: { id: 11 },
    })
    await store.dispatch('rowHistory/forceCreate', {
      ...scope,
      rowHistoryEntry: { id: 10 },
    })
    respond([200, { results: [{ id: 10 }], count: 1 }])
    await pending
    expect(
      store.state.rowHistory.entries.map((entry) => entry.id).sort()
    ).toEqual([10, 11])
    expect(store.getters['rowHistory/getTotalCount']).toBe(2)
  })

  test('a late response for the previous row cannot replace the current row', async () => {
    let respond
    testApp.mock.onGet(url).reply(
      () =>
        new Promise((resolve) => {
          respond = resolve
        })
    )
    testApp.mock.onGet('/database/rows/table/1/3/history/').reply(200, {
      results: [{ id: 30 }],
      count: 1,
    })
    const previous = store.dispatch('rowHistory/fetchInitial', scope)
    await vi.waitFor(() => expect(respond).toBeTypeOf('function'))
    await store.dispatch('rowHistory/fetchInitial', { tableId: 1, rowId: 3 })
    respond([200, { results: [{ id: 10 }], count: 1 }])
    await previous
    expect(store.state.rowHistory.loadedRowId).toBe(3)
    expect(store.state.rowHistory.entries).toEqual([{ id: 30 }])
  })

  test('a stale pagination response cannot append to a newly selected row', async () => {
    testApp.mock.onGet(url).replyOnce(200, { results: [{ id: 10 }], count: 2 })
    await store.dispatch('rowHistory/fetchInitial', scope)
    let respond
    testApp.mock.onGet(url).reply(
      () =>
        new Promise((resolve) => {
          respond = resolve
        })
    )
    const page = store.dispatch('rowHistory/fetchNextPage', scope)
    await vi.waitFor(() => expect(respond).toBeTypeOf('function'))
    testApp.mock.onGet('/database/rows/table/1/3/history/').reply(200, {
      results: [{ id: 30 }],
      count: 1,
    })
    await store.dispatch('rowHistory/fetchInitial', { tableId: 1, rowId: 3 })
    respond([200, { results: [{ id: 5 }], count: 2 }])
    await page
    expect(store.state.rowHistory.entries).toEqual([{ id: 30 }])
    expect(store.getters['rowHistory/getTotalCount']).toBe(1)
  })

  test('delayed entries outside the first page do not inflate counts or skip pagination', async () => {
    let respond
    testApp.mock.onGet(url).replyOnce(
      () =>
        new Promise((resolve) => {
          respond = resolve
        })
    )
    const pending = store.dispatch('rowHistory/fetchInitial', scope)
    await vi.waitFor(() => expect(respond).toBeTypeOf('function'))
    await store.dispatch('rowHistory/forceCreate', {
      ...scope,
      rowHistoryEntry: { id: 12, timestamp: '2026-09-07T10:00:00Z' },
    })
    // History IDs do not replace the action timestamp as the primary ordering.
    await store.dispatch('rowHistory/forceCreate', {
      ...scope,
      rowHistoryEntry: { id: 200, timestamp: '2026-09-07T10:00:00Z' },
    })
    const entries = Array.from({ length: 30 }, (_, index) => ({
      id: 100 - index,
      timestamp: '2026-09-08T10:00:00Z',
    }))
    respond([200, { results: entries, count: 100 }])
    await pending
    expect(store.state.rowHistory.entries).toEqual(entries)
    expect(store.getters['rowHistory/getTotalCount']).toBe(100)
    testApp.mock
      .onGet(url)
      .replyOnce(200, { results: [{ id: 70 }], count: 100 })
    await store.dispatch('rowHistory/fetchNextPage', scope)
    expect(testApp.mock.history.get[1].params.offset).toBe(30)
    expect(store.state.rowHistory.entries.at(-1).id).toBe(70)
  })

  test('failed recovery leaves history invalidated and clears its loading state', async () => {
    testApp.dontFailOnErrorResponses()
    testApp.mock.onGet(url).reply(503, {})
    await store.dispatch('rowHistory/invalidate')
    await expect(
      store.dispatch('rowHistory/fetchInitial', {
        ...scope,
        realtimeRecovery: true,
      })
    ).rejects.toThrow()
    expect(store.getters['rowHistory/getLoaded']).toBe(false)
    expect(store.getters['rowHistory/getLoading']).toBe(false)
    expect(
      testApp.mock.history.get[0].headers['X-Baserow-Realtime-Recovery']
    ).toBe('true')
  })

  test('same-row recovery keeps cached history until success and merges new live entries', async () => {
    testApp.mock.onGet(url).replyOnce(200, { results: [{ id: 10 }], count: 1 })
    await store.dispatch('rowHistory/fetchInitial', scope)
    let respond
    testApp.mock.onGet(url).replyOnce(
      () =>
        new Promise((resolve) => {
          respond = resolve
        })
    )
    await store.dispatch('rowHistory/invalidate')
    const pending = store.dispatch('rowHistory/fetchInitial', {
      ...scope,
      realtimeRecovery: true,
    })
    await vi.waitFor(() => expect(respond).toBeTypeOf('function'))
    expect(store.state.rowHistory.entries).toEqual([{ id: 10 }])
    expect(store.getters['rowHistory/getTotalCount']).toBe(1)
    await store.dispatch('rowHistory/forceCreate', {
      ...scope,
      rowHistoryEntry: { id: 12 },
    })
    respond([200, { results: [{ id: 11 }], count: 1 }])
    await pending
    expect(store.state.rowHistory.entries).toEqual([{ id: 11 }, { id: 12 }])
    expect(store.getters['rowHistory/getTotalCount']).toBe(2)

    await store.dispatch('rowHistory/invalidate')
    await store.dispatch('rowHistory/fetchNextPage', scope)
    expect(testApp.mock.history.get).toHaveLength(2)
  })
})
