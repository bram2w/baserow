import { TestApp } from '@baserow/test/helpers/testApp'
import { flushPromises } from '@vue/test-utils'
import DashboardFilterControl from '@baserow/modules/dashboard/components/filter/DashboardFilterControl'

let wrapper, testApp
beforeEach(() => {
  testApp = new TestApp()
})
afterEach(() => testApp.afterEach())
async function render({
  mode = 'dropdown',
  appliedValues = ['Design'],
  multiple = true,
  unavailable = [],
  editMode = false,
} = {}) {
  wrapper = await testApp.mount(DashboardFilterControl, {
    global: { stubs: { Teleport: false } },
    props: {
      filter: { id: 1, label: 'Team', operator: 'equal', mode, multiple },
      appliedValues,
      editMode,
      optionState: {
        results: ['Design', 'Sales'],
        unavailable,
        next: null,
        loading: false,
        error: false,
      },
    },
  })
  return wrapper
}

test('discards unapplied dropdown changes on close and restores applied choices', async () => {
  await render()
  await wrapper.get('.dropdown__selected').trigger('click')
  await flushPromises()
  await testApp.body.findAll('input[type="checkbox"]')[1].setValue(true)
  expect(wrapper.emitted('apply')).toBeUndefined()
  await testApp.body.get('form').trigger('keydown', { key: 'Escape' })
  await wrapper.get('.dropdown__selected').trigger('click')
  await flushPromises()
  const boxes = testApp.body.findAll('input[type="checkbox"]')
  expect(boxes[0].element.checked).toBe(true)
  expect(boxes[1].element.checked).toBe(false)
  expect(wrapper.emitted('options')).toHaveLength(2)
})

test('applies a cleared draft only after Update is pressed', async () => {
  await render()
  await wrapper.get('.dropdown__selected').trigger('click')
  await flushPromises()
  await testApp.body.get('input[type="checkbox"]').setValue(false)
  expect(wrapper.emitted('apply')).toBeUndefined()
  await testApp.body.get('form').trigger('submit')
  expect(wrapper.emitted('apply')).toEqual([[[]]])
  expect(wrapper.get('.dropdown__selected').attributes('aria-expanded')).toBe(
    'false'
  )
})

test('trims input on Apply and discards its unapplied edits', async () => {
  await render({ mode: 'input', appliedValues: [] })
  await wrapper.get('.dropdown__selected').trigger('click')
  await flushPromises()
  await testApp.body.get('input').setValue('  Design  ')
  await testApp.body.get('form').trigger('submit')
  expect(wrapper.emitted('apply')).toEqual([[['Design']]])
  await wrapper.get('.dropdown__selected').trigger('click')
  await flushPromises()
  expect(testApp.body.get('input').element.value).toBe('')
})

test('shows unavailable selections and lets them be removed', async () => {
  await render({ unavailable: ['Design'] })
  expect(wrapper.find('.dashboard-filter__info').exists()).toBe(true)
  await wrapper.get('.dropdown__selected').trigger('click')
  await flushPromises()
  expect(testApp.body.get('.dashboard-filter__unavailable').text()).toBe(
    'dashboardFilter.unavailable'
  )
  expect(testApp.body.get('input[type="checkbox"]').element.checked).toBe(true)
  await testApp.body.get('input[type="checkbox"]').setValue(false)
  await testApp.body.get('form').trigger('submit')
  expect(wrapper.emitted('apply')).toEqual([[[]]])
})

test('exposes the unavailable explanation on keyboard focus', async () => {
  await render({ unavailable: ['Design'] })
  await wrapper.get('.dropdown__selected').trigger('click')
  await flushPromises()
  const badge = testApp.body.get('.dashboard-filter__unavailable')
  expect(badge.attributes('tabindex')).toBe('0')
  await badge.trigger('focus')
  expect(document.body.querySelector('.tooltip').textContent).toBe(
    'dashboardFilter.unavailableHelp'
  )
  await badge.trigger('blur')
  expect(document.body.querySelector('.tooltip')).toBeNull()
})

test('a single-choice dropdown replaces the previous value', async () => {
  await render({ multiple: false })
  await wrapper.get('.dropdown__selected').trigger('click')
  await flushPromises()
  expect(testApp.body.find('input[type="checkbox"]').exists()).toBe(false)
  await testApp.body
    .findAll('.dashboard-filter__single-choice')[1]
    .trigger('click')
  await flushPromises()
  expect(wrapper.get('.dropdown__selected').attributes('aria-expanded')).toBe(
    'true'
  )
  expect(testApp.body.get('[aria-pressed="true"]').text()).toBe('Sales')
  await testApp.body.get('form').trigger('submit')
  expect(wrapper.emitted('apply')).toEqual([[['Sales']]])
})

test('opens the positioned context and restores trigger focus when Escape cancels the draft', async () => {
  await render()
  const trigger = wrapper.get('.dropdown__selected')
  await trigger.trigger('click')
  await flushPromises()
  expect(trigger.attributes('aria-expanded')).toBe('true')
  expect(testApp.body.get('.dashboard-filter__context').isVisible()).toBe(true)
  await testApp.body.findAll('input[type="checkbox"]')[1].setValue(true)
  await testApp.body.get('form').trigger('keydown', { key: 'Escape' })
  await flushPromises()
  expect(trigger.attributes('aria-expanded')).toBe('false')
  expect(document.activeElement).toBe(trigger.element)
  expect(wrapper.emitted('apply')).toBeUndefined()
  await trigger.trigger('click')
  await flushPromises()
  expect(
    testApp.body.findAll('input[type="checkbox"]')[1].element.checked
  ).toBe(false)
})

test('clears the applied selection without opening the picker', async () => {
  await render()
  await wrapper.get('[aria-label="dashboardFilter.clear"]').trigger('click')
  await flushPromises()
  expect(wrapper.emitted('apply')).toEqual([[[]]])
  expect(wrapper.emitted('options')).toBeUndefined()
  expect(wrapper.get('.dropdown__selected').attributes('aria-expanded')).toBe(
    'false'
  )
})

test('selects the filter settings in edit mode without opening the picker', async () => {
  await render({ editMode: true })
  await wrapper.get('[aria-label="dashboardFilter.settings"]').trigger('click')
  await flushPromises()
  expect(wrapper.emitted('select')).toHaveLength(1)
  await wrapper.get('.dropdown__selected').trigger('click')
  await flushPromises()
  expect(wrapper.emitted('select')).toHaveLength(2)
  expect(wrapper.emitted('options')).toBeUndefined()
  expect(wrapper.get('.dropdown__selected').attributes('aria-expanded')).toBe(
    'false'
  )
})

test('searches server options without applying or losing the current selection', async () => {
  await render()
  await wrapper.get('.dropdown__selected').trigger('click')
  await flushPromises()
  vi.useFakeTimers()
  try {
    await testApp.body.get('input[type="text"]').setValue('Sales')
    await vi.advanceTimersByTimeAsync(250)
    expect(wrapper.emitted('options').at(-1)).toEqual([
      { search: 'Sales', more: false, selected: ['Design'] },
    ])
    expect(wrapper.emitted('apply')).toBeUndefined()
    expect(testApp.body.get('input[type="checkbox"]').element.checked).toBe(
      true
    )
  } finally {
    vi.useRealTimers()
  }
})
