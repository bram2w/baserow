import { TestApp } from '@baserow/test/helpers/testApp'
import DashboardFormulaInput from '@baserow/modules/dashboard/components/DashboardFormulaInput'

let testApp
beforeEach(() => {
  testApp = new TestApp()
  testApp.store.commit('dashboardApplication/SET_FILTERS', [
    { id: 1, label: 'Country', mode: 'input' },
    { id: 2, label: 'Teams', mode: 'dropdown', multiple: true },
  ])
  testApp.store.commit('dashboardApplication/APPLY_FILTER', {
    filterId: 1,
    values: ['France'],
  })
  testApp.store.commit('dashboardApplication/APPLY_FILTER', {
    filterId: 2,
    values: ['Design', 'Marketing'],
  })
})
afterEach(() => testApp.afterEach())

test('exposes scalar and list values with readable names', () => {
  const provider = testApp.nuxtApp.$registry.get(
    'dashboardDataProvider',
    'dashboard_filter'
  )
  expect(provider.getDataChunk({}, ['1'])).toBe('France')
  expect(provider.getDataChunk({}, ['2'])).toEqual(['Design', 'Marketing'])
  expect(provider.getDataChunk({}, ['2', '1'])).toBe('Marketing')
  expect(
    provider.getNodes({}).nodes.map(({ name, type }) => ({ name, type }))
  ).toEqual([
    { name: 'Country', type: 'string' },
    { name: 'Teams', type: 'array' },
  ])
  expect(provider.getDataContent({ storePrefix: 'template/' })).toEqual({})
})

test('renders a dashboard filter reference in the shared formula input', async () => {
  const wrapper = await testApp.mount(DashboardFormulaInput, {
    props: {
      modelValue: { formula: "get('dashboard_filter.1')", mode: 'advanced' },
      dataProvidersAllowed: ['dashboard_filter'],
    },
    global: { provide: { dashboardApplicationContext: { storePrefix: '' } } },
  })
  expect(wrapper.get('.get-formula-component').text()).toContain('Country')
  expect(wrapper.find('.formula-input-field--error').exists()).toBe(false)
})

test.each([
  ['dashboard_filter', ['nope']],
  ['dashboard_filter', ['0']],
  ['dashboard_filter', ['1', 'extra']],
  ['table', ['nope']],
  ['table', ['1', 'result']],
  ['table', ['1', '*', 'field_0']],
])('rejects invalid %s paths', (type, path) => {
  expect(
    testApp.nuxtApp.$registry.get('dashboardDataProvider', type).isValid(path)
  ).toBe(false)
})

test('explores each widget table once, including fields unused by its aggregation', () => {
  const store = testApp.store
  const schema = {
    title: 'Orders',
    type: 'array',
    items: {
      type: 'object',
      properties: {
        field_11: { type: 'string', title: 'Country' },
        field_12: { type: 'number', title: 'Amount' },
      },
    },
  }
  store.commit('dashboardApplication/SET_WIDGETS', [
    { id: 1, data_source_id: 21 },
    { id: 2, data_source_id: 22 },
  ])
  store.commit('dashboardApplication/SET_DATA_SOURCES', [
    { id: 21, table_id: 10, table_schema: schema },
    { id: 22, table_id: 10, table_schema: schema },
    { id: 23, table_id: 20, table_schema: { ...schema, title: 'Unused' } },
  ])
  const provider = testApp.nuxtApp.$registry.get(
    'dashboardDataProvider',
    'table'
  )
  expect(provider.getDataSchema({})).toEqual({
    type: 'object',
    properties: { 10: { ...schema, order: 0 } },
  })
  expect(
    provider.getDataSchema({ storePrefix: 'template/' }).properties
  ).toEqual({})
})
