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
  canDelete = true,
} = {}) {
  wrapper = await testApp.mount(DashboardFilterControl, {
    global: { stubs: { Teleport: false } },
    props: {
      filter: { id: 1, label: 'Team', operator: 'equal', mode, multiple },
      appliedValues,
      editMode,
      canDelete,
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

test.each([true, false])(
  'keeps choices in their original order when selecting and deselecting (multiple: %s)',
  async (multiple) => {
    await render({ multiple, appliedValues: [] })
    await wrapper.get('.dropdown__selected').trigger('click')
    await flushPromises()
    const choices = () =>
      testApp.body
        .findAll('.dashboard-filter__option-value')
        .map((choice) => choice.text())
    const toggleSales = async (checked) => {
      if (multiple) {
        await testApp.body
          .findAll('input[type="checkbox"]')[1]
          .setValue(checked)
      } else {
        await testApp.body
          .findAll('.dashboard-filter__single-choice')[1]
          .trigger('click')
      }
    }
    expect(choices()).toEqual(['Design', 'Sales'])
    await toggleSales(true)
    expect(choices()).toEqual(['Design', 'Sales'])
    await toggleSales(false)
    expect(choices()).toEqual(['Design', 'Sales'])
    expect(wrapper.emitted('apply')).toBeUndefined()
  }
)

test('keeps a selected value missing from the loaded choices visible and removable', async () => {
  await render({
    appliedValues: ['Archived', 'Sales'],
    unavailable: ['Archived'],
  })
  await wrapper.get('.dropdown__selected').trigger('click')
  await flushPromises()
  expect(
    testApp.body
      .findAll('.dashboard-filter__option-value')
      .map((choice) => choice.text())
  ).toEqual(['Design', 'Sales', 'Archived'])
  const boxes = testApp.body.findAll('input[type="checkbox"]')
  expect(boxes[1].element.checked).toBe(true)
  expect(boxes[2].element.checked).toBe(true)
  await boxes[2].setValue(false)
  await testApp.body.get('form').trigger('submit')
  expect(wrapper.emitted('apply')).toEqual([[['Sales']]])
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
  await wrapper.get('.dropdown__selected').trigger('click')
  await flushPromises()
  expect(wrapper.emitted('select')).toHaveLength(1)
  expect(wrapper.emitted('options')).toBeUndefined()
  expect(wrapper.get('.dropdown__selected').attributes('aria-expanded')).toBe(
    'false'
  )
})

test('opens the deletion menu from the dots without selecting the filter or opening its choices', async () => {
  await render({ editMode: true })
  const trigger = wrapper.get('[aria-label="dashboardFilter.actions"]')
  await trigger.trigger('click')
  await flushPromises()
  expect(wrapper.emitted('select')).toBeUndefined()
  expect(wrapper.emitted('options')).toBeUndefined()
  const remove = testApp.body.get('.context__menu-item-link--delete')
  expect(remove.text()).toBe('dashboardFilter.delete')
  expect(document.activeElement).toBe(remove.element)
  await remove.trigger('keydown', { key: 'Escape' })
  await flushPromises()
  expect(trigger.attributes('aria-expanded')).toBe('false')
  expect(document.activeElement).toBe(trigger.element)
  expect(wrapper.emitted('delete')).toBeUndefined()
  await trigger.trigger('click')
  await flushPromises()
  await testApp.body.get('.context__menu-item-link--delete').trigger('click')
  expect(wrapper.emitted('delete')).toEqual([[]])
  expect(trigger.attributes('aria-expanded')).toBe('false')
})

test.each([
  { editMode: false, canDelete: true },
  { editMode: true, canDelete: false },
])(
  'hides deletion outside edit mode or without permission: %j',
  async (props) => {
    await render(props)
    expect(
      wrapper.find('[aria-label="dashboardFilter.actions"]').exists()
    ).toBe(false)
    expect(testApp.body.find('.context__menu-item-link--delete').exists()).toBe(
      false
    )
  }
)

test('filters loaded choices immediately without requesting options or losing selections', async () => {
  await render()
  await wrapper.get('.dropdown__selected').trigger('click')
  await flushPromises()
  const choices = () =>
    testApp.body
      .findAll('.dashboard-filter__option-value')
      .map((choice) => choice.text())
  const search = testApp.body.get('input[type="text"]')
  await search.setValue('sAL')
  expect(choices()).toEqual(['Sales'])
  expect(testApp.body.find('[role="status"]').exists()).toBe(false)
  expect(wrapper.emitted('options')).toHaveLength(1)
  expect(wrapper.emitted('apply')).toBeUndefined()

  await search.setValue('missing')
  expect(choices()).toEqual([])
  expect(testApp.body.text()).toContain('dashboardFilter.noOptions')
  await search.setValue('')
  expect(choices()).toEqual(['Design', 'Sales'])
  expect(testApp.body.get('input[type="checkbox"]').element.checked).toBe(true)
  expect(wrapper.emitted('options')).toHaveLength(1)
})
