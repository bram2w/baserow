import { TestApp } from '@baserow/test/helpers/testApp'
import { flushPromises } from '@vue/test-utils'
import { defineComponent } from 'vue'
import DashboardFilterSettings from '@baserow/modules/dashboard/components/filter/DashboardFilterSettings'

let testApp
beforeEach(() => {
  testApp = new TestApp()
})
afterEach(() => testApp.afterEach())

async function render(bindings = []) {
  const filter = {
    id: 5,
    dashboard_id: 1,
    label: 'Team',
    type: 'text',
    operator: 'equal',
    mode: 'dropdown',
    multiple: true,
    bindings,
  }
  const widgets = [
    { id: 2, data_source_id: 10, type: 'summary' },
    { id: 3, data_source_id: 11, type: 'summary' },
    { id: 4, data_source_id: 12, type: 'summary' },
  ]
  testApp.mock.onGet('/dashboard/1/widgets/').reply(200, widgets)
  testApp.mock.onGet('/dashboard/1/filters/').reply(200, [filter])
  testApp.mock.onGet('/dashboard/1/data-sources/').reply(200, [
    { id: 10, table_id: 20, integration_id: 1 },
    { id: 11, table_id: 20, integration_id: 1 },
    { id: 12, table_id: 30, integration_id: 1 },
  ])
  testApp.mock
    .onPost(/\/dashboard\/widgets\/\d+\/dispatch\//)
    .reply(200, { result: 1 })
  testApp.mock.onGet('/database/fields/table/20/').reply(200, [
    { id: 21, type: 'text', name: 'Team' },
    { id: 22, type: 'number', name: 'Budget' },
  ])
  testApp.mock
    .onGet('/database/fields/table/30/')
    .reply(200, [{ id: 31, type: 'text', name: 'Department' }])
  testApp.mock
    .onPatch('/dashboard/filters/5/')
    .reply(({ data }) => [200, { ...filter, ...JSON.parse(data) }])
  await testApp.store.dispatch('dashboardApplication/fetchInitial', {
    dashboardId: 1,
    forEditing: false,
  })
  testApp.store.commit('dashboardApplication/ADD_INTEGRATION', {
    id: 1,
    context_data: {
      databases: [
        {
          id: 1,
          name: 'Work',
          tables: [
            { id: 20, name: 'Projects' },
            { id: 30, name: 'Tasks' },
          ],
        },
      ],
    },
  })
  return testApp.mount(
    defineComponent({
      components: { DashboardFilterSettings },
      computed: {
        filter() {
          return this.$store.getters['dashboardApplication/getFilters'][0]
        },
      },
      template:
        '<DashboardFilterSettings :filter="filter" :dashboard="{ id: 1, workspace: { id: 1 } }" />',
    })
  )
}

test('configures one field per table in global settings and keeps other table mappings', async () => {
  const wrapper = await render()
  const rows = wrapper.findAll('.dashboard-filter-table-field')
  expect(rows).toHaveLength(2)
  expect(rows[0].text()).toContain('Projects')
  expect(rows[1].text()).toContain('Tasks')
  await rows[0].get('.dropdown__selected').trigger('click')
  const team = rows[0]
    .findAll('.select__item-link')
    .find((item) => item.text().includes('Team'))
  expect(rows[0].text()).not.toContain('Budget')
  await team.trigger('click')
  await flushPromises()
  expect(JSON.parse(testApp.mock.history.patch.at(-1).data)).toEqual({
    bindings: [{ table_id: 20, field_id: 21 }],
  })
  await rows[1].get('.dropdown__selected').trigger('click')
  await rows[1]
    .findAll('.select__item-link')
    .find((item) => item.text().includes('Department'))
    .trigger('click')
  await flushPromises()
  expect(JSON.parse(testApp.mock.history.patch.at(-1).data)).toEqual({
    bindings: [
      { table_id: 20, field_id: 21 },
      { table_id: 30, field_id: 31 },
    ],
  })
  expect(
    testApp.mock.history.get.filter(
      ({ url }) => url === '/database/fields/table/20/'
    )
  ).toHaveLength(1)
})

test('shows a deleted mapped field as unavailable in global settings', async () => {
  const wrapper = await render([{ table_id: 20, field_id: null }])
  const row = wrapper.get('.dashboard-filter-table-field')
  expect(row.get('.dropdown__selected-text').text()).toBe(
    'dashboardFilter.invalidField'
  )
  expect(row.get('.dashboard-filter-bindings__error').text()).toBe(
    'dashboardFilter.invalidFieldHelp'
  )
})

test('keeps a saved table field repairable after its last widget is removed', async () => {
  const wrapper = await render([{ table_id: 20, field_id: null }])
  testApp.mock
    .onGet('/dashboard/1/widgets/')
    .reply(200, [{ id: 4, data_source_id: 12, type: 'summary' }])
  await testApp.store.dispatch('dashboardApplication/fetchWidgets', 1)
  await flushPromises()
  const rows = wrapper.findAll('.dashboard-filter-table-field')
  expect(rows).toHaveLength(2)
  const projects = rows.find((row) => row.text().includes('Projects'))
  expect(projects.get('.dashboard-filter-bindings__error').text()).toBe(
    'dashboardFilter.invalidFieldHelp'
  )
})
