import MockAdapter from 'axios-mock-adapter'

describe('dashboard text filters', () => {
  let store, mock
  const dashboardId = 1
  const widgets = [
    { id: 2, dashboard_id: 1, data_source_id: 10, type: 'summary' },
    { id: 3, dashboard_id: 1, data_source_id: 10, type: 'summary' },
  ]
  const filter = {
    id: 5,
    dashboard_id: 1,
    label: 'Team',
    type: 'text',
    operator: 'equal',
    mode: 'dropdown',
    multiple: true,
    bindings: [{ table_id: 1, field_id: 20 }],
  }

  beforeEach(async () => {
    const { $store, $client } = useNuxtApp()
    store = $store
    mock = new MockAdapter($client, { onNoMatch: 'throwException' })
    mock.onGet('/dashboard/1/widgets/').reply(200, widgets)
    mock.onGet('/dashboard/1/filters/').reply(200, [filter])
    mock
      .onGet('/dashboard/1/data-sources/')
      .reply(200, [{ id: 10, dashboard_id: 1 }])
    mock.onPost('/dashboard/widgets/2/dispatch/').reply(200, { result: 10 })
    mock.onPost('/dashboard/widgets/3/dispatch/').reply(200, { result: 20 })
    mock
      .onPost('/dashboard/filters/5/options/')
      .reply(200, { results: [], next: null, available: [] })
    await store.dispatch('dashboardApplication/fetchInitial', {
      dashboardId,
      forEditing: false,
    })
  })
  afterEach(() => mock.restore())

  test('keeps separate results for widgets sharing a source and preserves values on refresh', async () => {
    await store.dispatch('dashboardApplication/applyFilter', {
      filterId: 5,
      values: ['Design'],
    })
    expect(store.getters['dashboardApplication/getDataForWidget'](2)).toEqual({
      result: 10,
    })
    expect(store.getters['dashboardApplication/getDataForWidget'](3)).toEqual({
      result: 20,
    })
    const lastDispatch = mock.history.post
      .filter(({ url }) => url.endsWith('/dispatch/'))
      .at(-1)
    expect(JSON.parse(lastDispatch.data)).toEqual({
      filters: [{ filter_id: 5, values: ['Design'] }],
    })
    await store.dispatch('dashboardApplication/refresh')
    expect(
      store.getters['dashboardApplication/getAppliedFilterValues'](5)
    ).toEqual(['Design'])
    await store.dispatch('dashboardApplication/fetchInitial', {
      dashboardId,
      forEditing: false,
    })
    expect(
      store.getters['dashboardApplication/getAppliedFilterValues'](5)
    ).toEqual([])
  })

  test('ignores a widget response from before the latest Apply', async () => {
    let resolveOld
    mock.onPost('/dashboard/widgets/2/dispatch/').reply(
      () =>
        new Promise((resolve) => {
          resolveOld = resolve
        })
    )
    const old = store.dispatch('dashboardApplication/applyFilter', {
      filterId: 5,
      values: ['Design'],
    })
    await vi.waitFor(() => expect(resolveOld).toBeTypeOf('function'))
    mock.onPost('/dashboard/widgets/2/dispatch/').reply(200, { result: 99 })
    await store.dispatch('dashboardApplication/applyFilter', {
      filterId: 5,
      values: ['Sales'],
    })
    resolveOld([200, { result: 1 }])
    await old
    expect(store.getters['dashboardApplication/getDataForWidget'](2)).toEqual({
      result: 99,
    })
  })

  test('ignores stale option searches and does not infer absence from failures', async () => {
    let resolveOld
    mock.onPost('/dashboard/filters/5/options/').reply(
      () =>
        new Promise((resolve) => {
          resolveOld = resolve
        })
    )
    const old = store.dispatch('dashboardApplication/fetchFilterOptions', {
      filterId: 5,
      search: 'old',
      selected: ['Design'],
    })
    await vi.waitFor(() => expect(resolveOld).toBeTypeOf('function'))
    mock
      .onPost('/dashboard/filters/5/options/')
      .reply(200, { results: ['Sales'], next: null, available: ['Design'] })
    await store.dispatch('dashboardApplication/fetchFilterOptions', {
      filterId: 5,
      search: 'Sales',
      selected: ['Design'],
    })
    resolveOld([200, { results: [], next: null, available: [] }])
    await old
    const options = () =>
      store.getters['dashboardApplication/getFilterOptions'](5)
    expect(options().results).toEqual(['Sales'])
    expect(options().unavailable).toEqual([])
    mock.onPost('/dashboard/filters/5/options/').reply(500)
    await store.dispatch('dashboardApplication/fetchFilterOptions', {
      filterId: 5,
      selected: ['Design'],
    })
    expect(options()).toMatchObject({
      error: true,
      loading: false,
      unavailable: [],
    })
  })

  test('ends an invalidated options request when configuration is refreshed', async () => {
    let resolveOptions
    mock.onPost('/dashboard/filters/5/options/').reply(
      () =>
        new Promise((resolve) => {
          resolveOptions = resolve
        })
    )
    const request = store.dispatch('dashboardApplication/fetchFilterOptions', {
      filterId: 5,
    })
    await vi.waitFor(() => expect(resolveOptions).toBeTypeOf('function'))
    await store.dispatch('dashboardApplication/fetchFilters')
    resolveOptions([200, { results: ['Old'], next: null, available: [] }])
    await request
    expect(
      store.getters['dashboardApplication/getFilterOptions'](5)
    ).toMatchObject({ loading: false, results: [] })
  })

  test('does not restore a deleted filter from a delayed update response', async () => {
    let resolveUpdate
    mock.onPatch('/dashboard/filters/5/').reply(
      () =>
        new Promise((resolve) => {
          resolveUpdate = resolve
        })
    )
    const update = store.dispatch('dashboardApplication/updateFilter', {
      filterId: 5,
      values: { label: 'Renamed' },
    })
    await vi.waitFor(() => expect(resolveUpdate).toBeTypeOf('function'))
    mock.onGet('/dashboard/1/filters/').reply(200, [])
    await store.dispatch('dashboardApplication/handleFiltersUpdated')
    resolveUpdate([200, { ...filter, label: 'Renamed' }])
    await update
    expect(store.getters['dashboardApplication/getFilters']).toEqual([])
  })
})
