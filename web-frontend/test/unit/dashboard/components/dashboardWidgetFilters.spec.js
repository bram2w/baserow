import { TestApp } from '@baserow/test/helpers/testApp'
import DashboardWidget from '@baserow/modules/dashboard/components/widget/DashboardWidget'

describe('widget filter indicator', () => {
  let testApp, store
  const dashboard = { id: 1, workspace: { id: 1 } }
  const widget = {
    id: 2,
    type: 'summary',
    title: 'Revenue',
    data_source_id: 10,
  }
  const filter = {
    id: 5,
    label: 'Country',
    type: 'text',
    operator: 'equal',
    mode: 'input',
    multiple: false,
  }
  const condition = {
    field: 20,
    type: 'equal',
    value: { formula: "get('dashboard_filter.5')", mode: 'simple' },
  }

  beforeEach(async () => {
    sessionStorage.clear()
    testApp = new TestApp()
    store = testApp.store
    testApp.mock.onGet('/dashboard/1/widgets/').reply(200, [widget])
    testApp.mock.onGet('/dashboard/1/filters/').reply(200, [filter])
    testApp.mock.onGet('/dashboard/1/data-sources/').reply(200, [
      { id: 10, type: 'local_baserow_aggregate_rows', filters: [condition] },
      { id: 11, type: 'local_baserow_aggregate_rows', filters: [] },
    ])
    testApp.mock
      .onPost('/dashboard/widgets/2/dispatch/')
      .reply(200, { result: 42 })
    await store.dispatch('dashboardApplication/fetchInitial', {
      dashboardId: 1,
      forEditing: false,
    })
  })

  afterEach(async () => {
    await testApp.afterEach()
    sessionStorage.clear()
  })

  const apply = (values) =>
    store.dispatch('dashboardApplication/applyFilter', { filterId: 5, values })

  const render = (values = widget) =>
    testApp.mount(DashboardWidget, {
      props: { dashboard, widget: values },
      global: { stubs: { SummaryWidget: true } },
    })

  test('shows the icon beside the title only after applying a linked filter', async () => {
    const wrapper = await render()
    const indicator = '.dashboard-widget__filter-status'
    expect(wrapper.find(indicator).exists()).toBe(false)

    await apply(['France'])
    const status = wrapper.get(indicator)
    expect(status.get('.iconoir-filter').exists()).toBe(true)
    expect(status.element.previousElementSibling.textContent).toBe('Revenue')
    expect(status.attributes('aria-label')).toBe('widget.filtered')
    expect(status.attributes('tabindex')).toBe('0')

    await status.trigger('mouseenter')
    expect(testApp.body.get('.tooltip__content').text()).toBe('widget.filtered')
    await status.trigger('mouseleave')
    await status.trigger('focus')
    expect(testApp.body.get('.tooltip__content').text()).toBe('widget.filtered')

    await apply([])
    expect(wrapper.find(indicator).exists()).toBe(false)
    expect(testApp.body.find('.tooltip__content').exists()).toBe(false)
  })

  test('does not mark a widget whose source does not use the active filter', async () => {
    const wrapper = await render({ ...widget, data_source_id: 11 })
    await apply(['France'])
    expect(wrapper.find('.dashboard-widget__filter-status').exists()).toBe(
      false
    )
  })

  test('removes the indicator when the control is deleted', async () => {
    const wrapper = await render()
    await apply(['France'])
    expect(wrapper.find('.dashboard-widget__filter-status').exists()).toBe(true)
    testApp.mock.onGet('/dashboard/1/filters/').reply(200, [])
    await store.dispatch('dashboardApplication/handleFiltersUpdated')
    expect(wrapper.find('.dashboard-widget__filter-status').exists()).toBe(
      false
    )
  })
})
