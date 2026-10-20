import { flushPromises } from '@vue/test-utils'
import { TestApp } from '@baserow/test/helpers/testApp'
import DashboardFilters from '@baserow/modules/dashboard/components/filter/DashboardFilters'

describe('dashboard filter persistence', () => {
  let testApp, store, mock
  let filters
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

  function startApp(userId = 1) {
    testApp = new TestApp()
    testApp.authenticate({ id: userId })
    store = testApp.store
    mock = testApp.mock
    for (const dashboardId of [1, 2]) {
      mock
        .onGet(`/dashboard/${dashboardId}/filters/`)
        .reply(() => [
          200,
          filters.filter((filter) => filter.dashboard_id === dashboardId),
        ])
      mock.onGet(`/dashboard/${dashboardId}/widgets/`).reply(200, [
        {
          id: dashboardId,
          dashboard_id: dashboardId,
          data_source_id: dashboardId,
          type: 'summary',
        },
      ])
      mock
        .onGet(`/dashboard/${dashboardId}/data-sources/`)
        .reply(200, [{ id: dashboardId, dashboard_id: dashboardId }])
      mock
        .onPost(`/dashboard/widgets/${dashboardId}/dispatch/`)
        .reply(200, { result: 10 })
    }
    mock.onPost(/\/dashboard\/filters\/[56]\/options\//).reply(200, {
      results: ['Design', 'Sales'],
      next: null,
      available: ['Design', 'Sales'],
    })
  }

  async function load(dashboardId = 1) {
    await store.dispatch('dashboardApplication/fetchInitial', {
      dashboardId,
      forEditing: false,
    })
    return testApp.mount(DashboardFilters, {
      global: { stubs: { Teleport: false } },
      props: { dashboard: { id: dashboardId, workspace: { id: 1 } } },
    })
  }

  async function reload(userId = 1) {
    await testApp.afterEach()
    startApp(userId)
    return load()
  }

  beforeEach(() => {
    sessionStorage.clear()
    filters = [{ ...filter }]
    startApp()
  })

  afterEach(async () => {
    vi.restoreAllMocks()
    await testApp.afterEach()
    sessionStorage.clear()
  })

  test.each([
    [{}, [' Design ', 'Sales'], [' Design ', 'Sales']],
    [{ multiple: false }, ['Design'], ['Design']],
    [{ mode: 'input' }, ['  Design  '], ['Design']],
  ])(
    'restores %j selections before the first widget request in a fresh app',
    async (config, values, expected) => {
      filters = [{ ...filter, ...config }]
      await load()
      await store.dispatch('dashboardApplication/applyFilter', {
        filterId: 5,
        values,
      })
      const wrapper = await reload()
      expect(wrapper.get('.dashboard-filter__value').text()).toBe(
        expected.length > 1 ? 'dashboardFilter.selections - 2' : 'Design'
      )
      const requests = mock.history.post.filter(({ url }) =>
        url.endsWith('/dispatch/')
      )
      expect(requests).toHaveLength(1)
      expect(JSON.parse(requests[0].data)).toEqual({
        filters: [{ filter_id: 5, values: expected }],
      })
      expect(
        mock.history.post
          .filter(({ url }) => url.endsWith('/options/'))
          .map(({ data }) => JSON.parse(data))
      ).toEqual(
        config.mode === 'input' ? [] : [{ search: '', selected: expected }]
      )
    }
  )

  test('keeps independent selections when navigating between dashboards', async () => {
    filters.push({ ...filter, id: 6, dashboard_id: 2 })
    let wrapper = await load()
    await store.dispatch('dashboardApplication/applyFilter', {
      filterId: 5,
      values: ['Design'],
    })
    wrapper.unmount()
    wrapper = await load(2)
    expect(wrapper.get('.dashboard-filter__value').text()).toBe(
      'dashboardFilter.choose'
    )
    await store.dispatch('dashboardApplication/applyFilter', {
      filterId: 6,
      values: ['Sales'],
    })
    wrapper.unmount()
    wrapper = await load()
    expect(wrapper.get('.dashboard-filter__value').text()).toBe('Design')
    wrapper.unmount()
    wrapper = await load(2)
    expect(wrapper.get('.dashboard-filter__value').text()).toBe('Sales')
  })

  test.each(['initial', 'realtime'])(
    'restores selections when a realtime update overlaps loading and %s finishes first',
    async (first) => {
      await load()
      await store.dispatch('dashboardApplication/applyFilter', {
        filterId: 5,
        values: ['Design'],
      })
      await testApp.afterEach()
      startApp()
      let finishInitial, finishRealtime
      let requestsStarted = 0
      mock.onGet('/dashboard/1/filters/').reply(() => {
        requestsStarted += 1
        if (requestsStarted <= 2) {
          return new Promise((resolve) => {
            if (requestsStarted === 1) finishInitial = resolve
            else finishRealtime = resolve
          })
        }
        return [200, filters]
      })
      const initial = load()
      await vi.waitFor(() => expect(finishInitial).toBeTypeOf('function'))
      const realtime = store.dispatch(
        'dashboardApplication/handleFiltersUpdated'
      )
      await vi.waitFor(() => expect(finishRealtime).toBeTypeOf('function'))
      if (first === 'initial') {
        finishInitial([200, filters])
        await initial
        finishRealtime([200, filters])
      } else {
        finishRealtime([200, filters])
        await realtime
        finishInitial([200, filters])
      }
      const wrapper = await initial
      await realtime
      await flushPromises()
      expect(wrapper.get('.dashboard-filter__value').text()).toBe('Design')
      const requests = mock.history.post.filter(({ url }) =>
        url.endsWith('/dispatch/')
      )
      expect(requests.length).toBeGreaterThan(0)
      for (const request of requests) {
        expect(JSON.parse(request.data)).toEqual({
          filters: [{ filter_id: 5, values: ['Design'] }],
        })
      }
    }
  )

  test('keeps selections separate for different signed-in users', async () => {
    await load()
    await store.dispatch('dashboardApplication/applyFilter', {
      filterId: 5,
      values: ['Design'],
    })
    let wrapper = await reload(2)
    expect(wrapper.get('.dashboard-filter__value').text()).toBe(
      'dashboardFilter.choose'
    )
    await store.dispatch('dashboardApplication/applyFilter', {
      filterId: 5,
      values: ['Sales'],
    })
    wrapper = await reload(1)
    expect(wrapper.get('.dashboard-filter__value').text()).toBe('Design')
  })

  test.each(['updateFilter', 'handleFiltersUpdated'])(
    'does not save an old user selection when a delayed %s finishes after switching accounts',
    async (action) => {
      await load()
      await store.dispatch('dashboardApplication/applyFilter', {
        filterId: 5,
        values: ['Design'],
      })
      let finish
      const response = () =>
        new Promise((resolve) => {
          finish = resolve
        })
      if (action === 'updateFilter') {
        mock.onPatch('/dashboard/filters/5/').reply(response)
      } else {
        mock.onGet('/dashboard/1/filters/').reply(response)
      }
      const pending = store.dispatch(`dashboardApplication/${action}`, {
        filterId: 5,
        values: { label: 'Renamed' },
      })
      await vi.waitFor(() => expect(finish).toBeTypeOf('function'))
      testApp.authenticate({ id: 2 })
      finish([
        200,
        action === 'updateFilter' ? { ...filter, label: 'Renamed' } : filters,
      ])
      await pending
      let wrapper = await reload(2)
      expect(wrapper.get('.dashboard-filter__value').text()).toBe(
        'dashboardFilter.choose'
      )
      wrapper = await reload(1)
      expect(wrapper.get('.dashboard-filter__value').text()).toBe('Design')
    }
  )

  test('restores the last applied selection without saving an open draft', async () => {
    let wrapper = await load()
    await store.dispatch('dashboardApplication/applyFilter', {
      filterId: 5,
      values: ['Design'],
    })
    await wrapper.get('.dropdown__selected').trigger('click')
    await flushPromises()
    await testApp.body.findAll('input[type="checkbox"]')[1].setValue(true)
    wrapper = await reload()
    expect(wrapper.get('.dashboard-filter__value').text()).toBe('Design')
    await wrapper.get('.dropdown__selected').trigger('click')
    await flushPromises()
    expect(
      testApp.body
        .findAll('input[type="checkbox"]')
        .map((checkbox) => checkbox.element.checked)
    ).toEqual([true, false])
  })

  test('does not restore a selection cleared with the cross', async () => {
    let wrapper = await load()
    await store.dispatch('dashboardApplication/applyFilter', {
      filterId: 5,
      values: ['Design'],
    })
    await wrapper.get('[aria-label="dashboardFilter.clear"]').trigger('click')
    await flushPromises()
    wrapper = await reload()
    expect(wrapper.get('.dashboard-filter__value').text()).toBe(
      'dashboardFilter.choose'
    )
  })

  test.each([
    [{}, { mode: 'input' }],
    [{}, { multiple: false }],
    [{ mode: 'input' }, { mode: 'dropdown' }],
    [{ multiple: false }, { multiple: true }],
  ])(
    'does not restore a selection reset by an update from %j to %j',
    async (initial, changes) => {
      filters = [{ ...filter, ...initial }]
      await load()
      await store.dispatch('dashboardApplication/applyFilter', {
        filterId: 5,
        values: ['Design'],
      })
      filters = [{ ...filter, ...initial, ...changes }]
      mock.onPatch('/dashboard/filters/5/').reply(200, filters[0])
      await store.dispatch('dashboardApplication/updateFilter', {
        filterId: 5,
        values: changes,
      })
      const wrapper = await reload()
      expect(wrapper.get('.dashboard-filter__value').text()).toBe(
        'dashboardFilter.choose'
      )
    }
  )

  test.each([
    [{}, { mode: 'input' }],
    [{}, { multiple: false }],
    [{ mode: 'input' }, { mode: 'dropdown' }],
    [{ multiple: false }, { multiple: true }],
  ])(
    'discards saved values if the server changed from %j to %j while the page was closed',
    async (initial, changes) => {
      filters = [{ ...filter, ...initial }]
      await load()
      await store.dispatch('dashboardApplication/applyFilter', {
        filterId: 5,
        values: ['Design'],
      })
      filters = [{ ...filter, ...initial, ...changes }]
      const wrapper = await reload()
      expect(wrapper.get('.dashboard-filter__value').text()).toBe(
        'dashboardFilter.choose'
      )
      expect(
        JSON.parse(
          mock.history.post.find(({ url }) => url.endsWith('/dispatch/')).data
        )
      ).toEqual({ filters: [] })
    }
  )

  test('does not resurrect selections after a filter is deleted and restored', async () => {
    await load()
    await store.dispatch('dashboardApplication/applyFilter', {
      filterId: 5,
      values: ['Design'],
    })
    filters = []
    let wrapper = await reload()
    expect(wrapper.find('.dashboard-filter').exists()).toBe(false)
    filters = [{ ...filter }]
    wrapper = await reload()
    expect(wrapper.get('.dashboard-filter__value').text()).toBe(
      'dashboardFilter.choose'
    )
  })

  test.each([
    'invalid-json',
    '{}',
    JSON.stringify([{ id: 5, mode: 'dropdown', multiple: true, values: 3 }]),
  ])(
    'opens the dashboard when the saved selection is invalid: %s',
    async (saved) => {
      await load()
      await store.dispatch('dashboardApplication/applyFilter', {
        filterId: 5,
        values: ['Design'],
      })
      sessionStorage.setItem(sessionStorage.key(0), saved)
      const wrapper = await reload()
      expect(wrapper.get('.dashboard-filter__value').text()).toBe(
        'dashboardFilter.choose'
      )
    }
  )

  test('still opens and filters the dashboard when browser storage is blocked', async () => {
    for (const method of ['getItem', 'setItem', 'removeItem']) {
      vi.spyOn(sessionStorage, method).mockImplementation(() => {
        throw new Error('Storage blocked')
      })
    }
    const wrapper = await load()
    await store.dispatch('dashboardApplication/applyFilter', {
      filterId: 5,
      values: ['Design'],
    })
    await flushPromises()
    expect(wrapper.get('.dashboard-filter__value').text()).toBe('Design')
    await wrapper.get('[aria-label="dashboardFilter.clear"]').trigger('click')
    await flushPromises()
    expect(wrapper.get('.dashboard-filter__value').text()).toBe(
      'dashboardFilter.choose'
    )
  })
})
