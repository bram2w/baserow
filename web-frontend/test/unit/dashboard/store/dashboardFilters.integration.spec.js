import { flushPromises } from '@vue/test-utils'
import { TestApp } from '@baserow/test/helpers/testApp'
import DashboardFilters from '@baserow/modules/dashboard/components/filter/DashboardFilters'

describe('dashboard text filters', () => {
  let store, mock, testApp
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
    testApp = new TestApp()
    store = testApp.store
    mock = testApp.mock
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
  afterEach(() => testApp.afterEach())

  test.each([{ results: [] }, { results: ['Design'] }])(
    'reuses loaded options $results until Refresh while preserving selections',
    async ({ results }) => {
      mock
        .onPost('/dashboard/filters/5/options/')
        .reply(200, { results, next: null, available: ['Design'] })
      const open = () =>
        store.dispatch('dashboardApplication/fetchFilterOptions', {
          filterId: 5,
          useCache: true,
        })
      await open()
      await store.dispatch('dashboardApplication/applyFilter', {
        filterId: 5,
        values: ['Design'],
      })
      mock
        .onPost('/dashboard/filters/5/options/')
        .reply(200, { results: ['Sales'], next: null, available: [] })
      await open()
      expect(
        store.getters['dashboardApplication/getFilterOptions'](5)
      ).toMatchObject({ results, loading: false })
      expect(
        mock.history.post.filter(({ url }) => url.endsWith('/options/'))
      ).toHaveLength(1)

      await store.dispatch('dashboardApplication/refresh')
      await open()
      expect(
        store.getters['dashboardApplication/getFilterOptions'](5)
      ).toMatchObject({
        results: ['Sales'],
        unavailable: ['Design'],
        loading: false,
      })
      expect(
        store.getters['dashboardApplication/getAppliedFilterValues'](5)
      ).toEqual(['Design'])
      expect(
        mock.history.post.filter(({ url }) => url.endsWith('/options/'))
      ).toHaveLength(2)
    }
  )

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

  test('reopens the picker and clears a search using the already loaded pages', async () => {
    mock.onPost('/dashboard/filters/5/options/').reply(({ data }) => {
      const { search, after } = JSON.parse(data)
      return [
        200,
        {
          results: search || after ? ['Sales'] : ['Design'],
          next: search ? null : after ? 'Sales' : 'Design',
          available: [],
        },
      ]
    })
    const wrapper = await testApp.mount(DashboardFilters, {
      global: { stubs: { Teleport: false } },
      props: { dashboard: { id: dashboardId } },
    })
    const open = async () => {
      await wrapper.get('.dropdown__selected').trigger('click')
      await flushPromises()
    }
    const search = async (value) => {
      vi.useFakeTimers()
      try {
        await testApp.body.get('input[type="text"]').setValue(value)
        await vi.advanceTimersByTimeAsync(250)
      } finally {
        vi.useRealTimers()
      }
      await flushPromises()
    }
    const choices = () =>
      testApp.body
        .findAll('.dashboard-filter__option-value')
        .map((v) => v.text())
    const optionRequests = () =>
      mock.history.post.filter(({ url }) => url.endsWith('/options/'))

    await open()
    await testApp.body.get('.dashboard-filter__more').trigger('click')
    await flushPromises()
    expect(choices()).toEqual(['Design', 'Sales'])
    expect(JSON.parse(optionRequests()[1].data).after).toBe('Design')
    await search('Sales')
    expect(choices()).toEqual(['Sales'])
    await search('')
    expect(choices()).toEqual(['Design', 'Sales'])
    expect(optionRequests()).toHaveLength(3)

    await search('Sales')
    await testApp.body.get('form').trigger('keydown', { key: 'Escape' })
    await open()
    expect(testApp.body.get('input[type="text"]').element.value).toBe('')
    expect(choices()).toEqual(['Design', 'Sales'])
    expect(testApp.body.find('[role="status"]').exists()).toBe(false)
    expect(optionRequests()).toHaveLength(4)
    await testApp.body.get('.dashboard-filter__more').trigger('click')
    await flushPromises()
    expect(JSON.parse(optionRequests()[4].data).after).toBe('Sales')
  })

  test('reopening does not restart an initial load or an explicit Refresh', async () => {
    let resolveOptions
    mock.onPost('/dashboard/filters/5/options/').reply(
      () =>
        new Promise((resolve) => {
          resolveOptions = resolve
        })
    )
    const open = () =>
      store.dispatch('dashboardApplication/fetchFilterOptions', {
        filterId: 5,
        useCache: true,
      })
    const initial = open()
    await vi.waitFor(() => expect(resolveOptions).toBeTypeOf('function'))
    await open()
    expect(
      mock.history.post.filter(({ url }) => url.endsWith('/options/'))
    ).toHaveLength(1)
    resolveOptions([200, { results: ['Design'], next: null, available: [] }])
    await initial

    resolveOptions = undefined
    const refresh = store.dispatch('dashboardApplication/refresh')
    await vi.waitFor(() => expect(resolveOptions).toBeTypeOf('function'))
    await open()
    resolveOptions([200, { results: ['Sales'], next: null, available: [] }])
    await refresh
    await open()
    expect(
      mock.history.post.filter(({ url }) => url.endsWith('/options/'))
    ).toHaveLength(2)
    expect(
      store.getters['dashboardApplication/getFilterOptions'](5)
    ).toMatchObject({
      results: ['Sales'],
      loading: false,
    })
  })

  test('ignores a pending search after restoring the unfiltered choices', async () => {
    mock.onPost('/dashboard/filters/5/options/').reply(200, {
      results: ['Design', 'Sales'],
      next: null,
      available: [],
    })
    await store.dispatch('dashboardApplication/fetchFilterOptions', {
      filterId: 5,
    })
    let resolveSearch
    mock.onPost('/dashboard/filters/5/options/').reply(
      () =>
        new Promise((resolve) => {
          resolveSearch = resolve
        })
    )
    const pending = store.dispatch('dashboardApplication/fetchFilterOptions', {
      filterId: 5,
      search: 'Sales',
    })
    await vi.waitFor(() => expect(resolveSearch).toBeTypeOf('function'))
    await store.dispatch('dashboardApplication/fetchFilterOptions', {
      filterId: 5,
      useCache: true,
    })
    resolveSearch([200, { results: ['Sales'], next: null, available: [] }])
    await pending
    expect(
      store.getters['dashboardApplication/getFilterOptions'](5)
    ).toMatchObject({
      results: ['Design', 'Sales'],
      search: '',
      loading: false,
    })
  })

  test.each(['search', 'refresh'])(
    'keeps the Refresh cache during a newer search when %s finishes first',
    async (first) => {
      await store.dispatch('dashboardApplication/applyFilter', {
        filterId: 5,
        values: ['Design'],
      })
      await store.dispatch('dashboardApplication/fetchFilterOptions', {
        filterId: 5,
      })
      const responses = {}
      mock.onPost('/dashboard/filters/5/options/').reply(
        ({ data }) =>
          new Promise((resolve) => {
            responses[JSON.parse(data).search ? 'search' : 'refresh'] = resolve
          })
      )
      const refresh = store.dispatch('dashboardApplication/refresh')
      await vi.waitFor(() => expect(responses.refresh).toBeTypeOf('function'))
      const search = store.dispatch('dashboardApplication/fetchFilterOptions', {
        filterId: 5,
        search: 'Sales',
      })
      await vi.waitFor(() => expect(responses.search).toBeTypeOf('function'))
      const options = () =>
        store.getters['dashboardApplication/getFilterOptions'](5)
      const finishSearch = () =>
        responses.search([
          200,
          { results: ['Sales'], next: null, available: ['Design'] },
        ])
      if (first === 'search') {
        finishSearch()
        await search
      }
      responses.refresh([
        200,
        { results: ['Marketing'], next: null, available: [] },
      ])
      await refresh
      if (first === 'search') {
        expect(options().results).toEqual(['Sales'])
      }
      await store.dispatch('dashboardApplication/fetchFilterOptions', {
        filterId: 5,
        useCache: true,
      })
      if (first === 'refresh') {
        finishSearch()
        await search
      }
      expect(options()).toMatchObject({
        results: ['Marketing'],
        search: '',
        loading: false,
        unavailable: first === 'search' ? [] : ['Design'],
      })
      expect(
        mock.history.post.filter(({ url }) => url.endsWith('/options/'))
      ).toHaveLength(3)
    }
  )

  test.each([200, 500])(
    'reopening during a search rejoins the pending Refresh returning %s',
    async (status) => {
      await store.dispatch('dashboardApplication/fetchFilterOptions', {
        filterId: 5,
      })
      const responses = {}
      mock.onPost('/dashboard/filters/5/options/').reply(
        ({ data }) =>
          new Promise((resolve) => {
            responses[JSON.parse(data).search ? 'search' : 'refresh'] = resolve
          })
      )
      const refresh = store.dispatch('dashboardApplication/refresh')
      await vi.waitFor(() => expect(responses.refresh).toBeTypeOf('function'))
      const search = store.dispatch('dashboardApplication/fetchFilterOptions', {
        filterId: 5,
        search: 'Sales',
      })
      await vi.waitFor(() => expect(responses.search).toBeTypeOf('function'))
      await store.dispatch('dashboardApplication/fetchFilterOptions', {
        filterId: 5,
        useCache: true,
      })
      expect(
        mock.history.post.filter(({ url }) => url.endsWith('/options/'))
      ).toHaveLength(3)
      responses.search([200, { results: ['Sales'], next: null, available: [] }])
      await search
      responses.refresh([
        status,
        { results: ['Marketing'], next: null, available: [] },
      ])
      await refresh
      expect(
        store.getters['dashboardApplication/getFilterOptions'](5)
      ).toMatchObject({
        results: status === 200 ? ['Marketing'] : [],
        search: '',
        loading: false,
        error: status !== 200,
      })
    }
  )

  test.each(['updateFilter', 'handleFiltersUpdated'])(
    'invalidates cached choices after %s changes the filter configuration',
    async (action) => {
      mock.onPost('/dashboard/filters/5/options/').reply(200, {
        results: ['Design'],
        next: null,
        available: [],
      })
      const open = () =>
        store.dispatch('dashboardApplication/fetchFilterOptions', {
          filterId: 5,
          useCache: true,
        })
      await open()
      const changed = { ...filter, bindings: [{ table_id: 1, field_id: 21 }] }
      mock.onPatch('/dashboard/filters/5/').reply(200, changed)
      mock.onGet('/dashboard/1/filters/').reply(200, [changed])
      await store.dispatch(`dashboardApplication/${action}`, {
        filterId: 5,
        values: { bindings: changed.bindings },
      })
      mock.onPost('/dashboard/filters/5/options/').reply(200, {
        results: ['Marketing'],
        next: null,
        available: [],
      })
      await open()
      expect(
        store.getters['dashboardApplication/getFilterOptions'](5).results
      ).toEqual(['Marketing'])
      expect(
        mock.history.post.filter(({ url }) => url.endsWith('/options/'))
      ).toHaveLength(2)
    }
  )

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
