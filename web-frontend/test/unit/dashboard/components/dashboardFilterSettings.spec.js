import { TestApp } from '@baserow/test/helpers/testApp'
import { flushPromises } from '@vue/test-utils'
import { defineComponent } from 'vue'
import DashboardFilterSettings from '@baserow/modules/dashboard/components/filter/DashboardFilterSettings'
import DashboardFilters from '@baserow/modules/dashboard/components/filter/DashboardFilters'

let testApp
beforeEach(() => {
  testApp = new TestApp()
})
afterEach(() => testApp.afterEach())

async function render(bindings = [], configuration = {}) {
  const filter = {
    id: 5,
    dashboard_id: 1,
    label: 'Team',
    type: 'text',
    operator: 'equal',
    mode: 'dropdown',
    multiple: true,
    ...configuration,
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
  testApp.mock.onPost('/dashboard/filters/5/options/').reply(200, {
    results: ['Design', 'Sales'],
    next: null,
    available: ['Design', 'Sales'],
  })
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
      components: { DashboardFilterSettings, DashboardFilters },
      computed: {
        filter() {
          return this.$store.getters['dashboardApplication/getFilters'][0]
        },
      },
      template: `<div>
          <DashboardFilters :dashboard="{ id: 1, workspace: { id: 1 } }" />
          <DashboardFilterSettings v-if="filter" :filter="filter" :dashboard="{ id: 1, workspace: { id: 1 } }" />
        </div>`,
    }),
    { global: { stubs: { Teleport: false } } }
  )
}

test.each(['cancel', 'close', 'escape'])(
  'asks before changing the format and preserves the selection on %s',
  async (dismiss) => {
    const wrapper = await render()
    await testApp.store.dispatch('dashboardApplication/applyFilter', {
      filterId: 5,
      values: ['Design'],
    })
    await wrapper.findAll('.segment-control__button')[1].trigger('click')
    expect(testApp.body.get('.modal__box').text()).toContain(
      'dashboardFilter.confirmResetMessage'
    )
    expect(testApp.mock.history.patch).toHaveLength(0)
    expect(wrapper.get('.dashboard-filter__value').text()).toBe('Design')
    expect(wrapper.get('.segment-control__button--active').text()).toBe(
      'dashboardFilter.dropdown'
    )
    if (dismiss === 'cancel') {
      await modalButton('action.cancel').trigger('click')
    } else if (dismiss === 'close') {
      await testApp.body.get('.modal__close').trigger('click')
    } else {
      window.dispatchEvent(new KeyboardEvent('keyup', { key: 'Escape' }))
    }
    await vi.waitFor(() =>
      expect(testApp.body.find('.modal__box').exists()).toBe(false)
    )
    expect(testApp.mock.history.patch).toHaveLength(0)
    expect(wrapper.get('.dashboard-filter__value').text()).toBe('Design')
  }
)

function modalButton(label) {
  return testApp.body
    .get('.modal__box')
    .findAll('button')
    .find((button) => button.text() === label)
}

test.each([
  [{}, 'input', { mode: 'input' }, 'confirmInputTitle', 'confirmInput'],
  [
    { mode: 'input' },
    'dropdown',
    { mode: 'dropdown' },
    'confirmDropdownTitle',
    'confirmDropdown',
  ],
  [{}, 'single', { multiple: false }, 'confirmSingleTitle', 'confirmSingle'],
  [
    { multiple: false },
    'multiple',
    { multiple: true },
    'confirmMultipleTitle',
    'confirmMultiple',
  ],
])(
  'clears values only after confirming the change from %j to %s',
  async (configuration, target, changes, title, action) => {
    const wrapper = await render([], configuration)
    await testApp.store.dispatch('dashboardApplication/applyFilter', {
      filterId: 5,
      values: ['Design'],
    })
    testApp.mock.resetHistory()
    await wrapper
      .findAll('.segment-control__button')
      .find((button) => button.text() === `dashboardFilter.${target}`)
      .trigger('click')
    expect(testApp.body.get('.modal__box').text()).toContain(
      configuration.mode === 'input'
        ? 'dashboardFilter.confirmResetInputMessage'
        : 'dashboardFilter.confirmResetMessage'
    )
    expect(testApp.body.get('.modal__box h2').text()).toBe(
      `dashboardFilter.${title}`
    )
    expect(testApp.mock.history.patch).toHaveLength(0)
    expect(testApp.mock.history.post).toHaveLength(0)
    expect(wrapper.get('.dashboard-filter__value').text()).toBe('Design')
    await modalButton(`dashboardFilter.${action}`).trigger('click')
    await vi.waitFor(() => {
      expect(wrapper.get('.dashboard-filter__value').text()).toBe(
        'dashboardFilter.choose'
      )
      expect(testApp.body.find('.modal__box').exists()).toBe(false)
    })
    expect(testApp.mock.history.patch).toHaveLength(1)
    expect(JSON.parse(testApp.mock.history.patch[0].data)).toEqual(changes)
    expect(
      JSON.parse(
        testApp.mock.history.post.find(({ url }) => url.endsWith('/dispatch/'))
          .data
      )
    ).toEqual({ filters: [] })
  }
)

test('confirms format changes even with no values, but ignores the current format', async () => {
  const wrapper = await render()
  await wrapper.findAll('.segment-control__button')[0].trigger('click')
  expect(testApp.body.find('.modal__box').exists()).toBe(false)
  expect(testApp.mock.history.patch).toHaveLength(0)
  await wrapper.findAll('.segment-control__button')[1].trigger('click')
  expect(testApp.body.find('.modal__box').exists()).toBe(true)
  await modalButton('dashboardFilter.confirmInput').trigger('click')
  await vi.waitFor(() =>
    expect(testApp.body.find('.modal__box').exists()).toBe(false)
  )
  expect(wrapper.get('.segment-control__button--active').text()).toBe(
    'dashboardFilter.input'
  )
})

test('prevents duplicate saves and preserves values if the confirmed change fails', async () => {
  testApp.dontFailOnErrorResponses()
  const wrapper = await render()
  await testApp.store.dispatch('dashboardApplication/applyFilter', {
    filterId: 5,
    values: ['Design'],
  })
  let finish
  testApp.mock.onPatch('/dashboard/filters/5/').reply(
    () =>
      new Promise((resolve) => {
        finish = resolve
      })
  )
  await wrapper.findAll('.segment-control__button')[1].trigger('click')
  await modalButton('dashboardFilter.confirmInput').trigger('click')
  await vi.waitFor(() => expect(finish).toBeTypeOf('function'))
  await modalButton('dashboardFilter.confirmInput').trigger('click')
  expect(testApp.mock.history.patch).toHaveLength(1)
  expect(modalButton('action.cancel').element.disabled).toBe(true)
  expect(testApp.body.find('.modal__close').exists()).toBe(false)
  window.dispatchEvent(new KeyboardEvent('keyup', { key: 'Escape' }))
  expect(testApp.body.find('.modal__box').exists()).toBe(true)
  expect(wrapper.get('.dashboard-filter__value').text()).toBe('Design')
  finish([500])
  await vi.waitFor(() =>
    expect(modalButton('dashboardFilter.confirmInput').element.disabled).toBe(
      false
    )
  )
  expect(wrapper.get('.dashboard-filter__value').text()).toBe('Design')
  expect(wrapper.get('.segment-control__button--active').text()).toBe(
    'dashboardFilter.dropdown'
  )
  await modalButton('action.cancel').trigger('click')
  await vi.waitFor(() =>
    expect(testApp.body.find('.modal__box').exists()).toBe(false)
  )
})

test('dismisses a pending confirmation if the format changes in another tab', async () => {
  const wrapper = await render()
  await wrapper.findAll('.segment-control__button')[1].trigger('click')
  const filter = testApp.store.getters['dashboardApplication/getFilters'][0]
  testApp.mock
    .onGet('/dashboard/1/filters/')
    .reply(200, [{ ...filter, multiple: false }])
  await testApp.store.dispatch('dashboardApplication/handleFiltersUpdated')
  await vi.waitFor(() =>
    expect(testApp.body.find('.modal__box').exists()).toBe(false)
  )
  expect(testApp.mock.history.patch).toHaveLength(0)
  expect(wrapper.get('.segment-control__button--active').text()).toBe(
    'dashboardFilter.dropdown'
  )
  expect(wrapper.findAll('.segment-control__button--active')[1].text()).toBe(
    'dashboardFilter.single'
  )
})

test('keeps confirmation open when an earlier label save finishes', async () => {
  const wrapper = await render()
  const filter = testApp.store.getters['dashboardApplication/getFilters'][0]
  let finish
  testApp.mock.onPatch('/dashboard/filters/5/').reply(
    () =>
      new Promise((resolve) => {
        finish = resolve
      })
  )
  const label = wrapper.get('.dashboard-filter-settings input')
  await label.setValue('Department')
  await label.trigger('blur')
  await vi.waitFor(() => expect(finish).toBeTypeOf('function'))
  await wrapper.findAll('.segment-control__button')[1].trigger('click')
  expect(testApp.body.find('.modal__box').exists()).toBe(true)
  finish([200, { ...filter, label: 'Department' }])
  await flushPromises()
  await vi.waitFor(() =>
    expect(wrapper.get('.dashboard-filter label').text()).toBe('Department')
  )
  await new Promise((resolve) => setTimeout(resolve, 0))
  expect(testApp.body.find('.modal__box').exists()).toBe(true)
  await modalButton('action.cancel').trigger('click')
  await vi.waitFor(() =>
    expect(testApp.body.find('.modal__box').exists()).toBe(false)
  )
})

test('cleans up the open confirmation when the filter is removed remotely', async () => {
  const wrapper = await render()
  await wrapper.findAll('.segment-control__button')[1].trigger('click')
  expect(testApp.body.find('.modal__box').exists()).toBe(true)
  expect(document.body.classList.contains('prevent-scroll')).toBe(true)
  testApp.mock.onGet('/dashboard/1/filters/').reply(200, [])
  await testApp.store.dispatch('dashboardApplication/handleFiltersUpdated')
  await flushPromises()
  expect(testApp.body.find('.modal__box').exists()).toBe(false)
  expect(document.body.classList.contains('prevent-scroll')).toBe(false)
  expect(testApp.mock.history.patch).toHaveLength(0)
})

test('offers only a table formula for dropdown values', async () => {
  const wrapper = await render()
  expect(wrapper.text()).toContain('dashboardFilter.sourceOptionsHelp')
  expect(wrapper.findAll('.formula-input-field')).toHaveLength(1)
  expect(wrapper.text()).not.toContain('dashboardFilter.manualOptions')
  expect(wrapper.text()).not.toContain('dashboardFilter.addOption')
})

test('saves the shared operator without clearing selected values', async () => {
  const wrapper = await render()
  await testApp.store.dispatch('dashboardApplication/applyFilter', {
    filterId: 5,
    values: ['Design'],
  })
  await wrapper
    .findAll('.dashboard-filter-settings .dropdown__selected')[1]
    .trigger('click')
  const items = testApp.body.findAll('.select__item-link')
  expect(items.some((item) => item.text() === 'viewFilter.startsWith')).toBe(
    true
  )
  expect(items.some((item) => item.text() === 'viewFilter.isAnyOf')).toBe(false)
  await items
    .find((item) => item.text() === 'viewFilter.isNot')
    .trigger('click')
  await flushPromises()
  expect(JSON.parse(testApp.mock.history.patch.at(-1).data)).toEqual({
    operator: 'not_equal',
  })
  expect(wrapper.get('.dashboard-filter__value').text()).toBe('Design')
  expect(testApp.body.find('.modal__box').exists()).toBe(false)
})

test('confirms resetting values before switching to an empty check', async () => {
  const wrapper = await render()
  await testApp.store.dispatch('dashboardApplication/applyFilter', {
    filterId: 5,
    values: ['Design'],
  })
  await wrapper
    .findAll('.dashboard-filter-settings .dropdown__selected')[1]
    .trigger('click')
  await testApp.body
    .findAll('.select__item-link')
    .find((item) => item.text() === 'viewFilter.isEmpty')
    .trigger('click')
  expect(testApp.mock.history.patch).toHaveLength(0)
  await modalButton('dashboardFilter.confirmOperator').trigger('click')
  await flushPromises()
  expect(wrapper.get('.dashboard-filter__value').text()).toBe(
    'dashboardFilter.inactive'
  )
  expect(wrapper.find('.segment-control').exists()).toBe(false)
  expect(wrapper.find('.formula-input-field').exists()).toBe(false)
})
