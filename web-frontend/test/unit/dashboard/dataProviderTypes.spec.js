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
  ['data_source', ['nope']],
])('rejects invalid %s paths', (type, path) => {
  expect(
    testApp.nuxtApp.$registry.get('dashboardDataProvider', type).isValid(path)
  ).toBe(false)
})
