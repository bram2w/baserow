import { TestApp } from '@baserow/test/helpers/testApp'
import { flushPromises } from '@vue/test-utils'
import DashboardFilterControl from '@baserow/modules/dashboard/components/filter/DashboardFilterControl'

const ContextStub = {
  data: () => ({ open: false }),
  emits: ['shown', 'hidden'],
  methods: {
    toggle() {
      this.open = !this.open
      this.$emit(this.open ? 'shown' : 'hidden')
    },
    hide() {
      this.open = false
      this.$emit('hidden')
    },
  },
  template:
    '<div v-if="open" data-testid="panel"><slot /><button data-testid="close" @click="hide">Close</button></div>',
}
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
} = {}) {
  wrapper = await testApp.mount(DashboardFilterControl, {
    props: {
      filter: { id: 1, label: 'Team', operator: 'equal', mode, multiple },
      appliedValues,
      optionState: {
        results: ['Design', 'Sales'],
        unavailable,
        next: null,
        loading: false,
        error: false,
      },
    },
    global: {
      stubs: { Context: ContextStub },
    },
  })
  return wrapper
}

test('discards unapplied dropdown changes on close and restores applied choices', async () => {
  await render()
  await wrapper.get('.dashboard-filter__trigger').trigger('click')
  await wrapper.findAll('input[type="checkbox"]')[1].setValue(true)
  expect(wrapper.emitted('apply')).toBeUndefined()
  await wrapper.get('[data-testid="close"]').trigger('click')
  await wrapper.get('.dashboard-filter__trigger').trigger('click')
  const boxes = wrapper.findAll('input[type="checkbox"]')
  expect(boxes[0].element.checked).toBe(true)
  expect(boxes[1].element.checked).toBe(false)
  expect(wrapper.emitted('options')).toHaveLength(2)
})

test('applies a cleared draft only after Update is pressed', async () => {
  await render()
  await wrapper.get('.dashboard-filter__trigger').trigger('click')
  await wrapper.get('input[type="checkbox"]').setValue(false)
  expect(wrapper.emitted('apply')).toBeUndefined()
  await wrapper.get('form').trigger('submit')
  expect(wrapper.emitted('apply')).toEqual([[[]]])
  expect(wrapper.find('[data-testid="panel"]').exists()).toBe(false)
})

test('trims input on Apply and discards its unapplied edits', async () => {
  await render({ mode: 'input', appliedValues: [] })
  await wrapper.get('.dashboard-filter__trigger').trigger('click')
  await wrapper.get('input').setValue('  Design  ')
  await wrapper.get('form').trigger('submit')
  expect(wrapper.emitted('apply')).toEqual([[['Design']]])
  await wrapper.get('.dashboard-filter__trigger').trigger('click')
  await flushPromises()
  expect(wrapper.get('input').element.value).toBe('')
})

test('shows unavailable selections and lets them be removed', async () => {
  await render({ unavailable: ['Design'] })
  expect(wrapper.find('.dashboard-filter__info').exists()).toBe(true)
  await wrapper.get('.dashboard-filter__trigger').trigger('click')
  expect(wrapper.get('.dashboard-filter__unavailable').text()).toBe(
    'dashboardFilter.unavailable'
  )
  expect(wrapper.get('input[type="checkbox"]').element.checked).toBe(true)
  await wrapper.get('input[type="checkbox"]').setValue(false)
  await wrapper.get('form').trigger('submit')
  expect(wrapper.emitted('apply')).toEqual([[[]]])
})

test('exposes the unavailable explanation on keyboard focus', async () => {
  await render({ unavailable: ['Design'] })
  await wrapper.get('.dashboard-filter__trigger').trigger('click')
  const badge = wrapper.get('.dashboard-filter__unavailable')
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
  await wrapper.get('.dashboard-filter__trigger').trigger('click')
  await wrapper.findAll('input[type="checkbox"]')[1].setValue(true)
  await wrapper.get('form').trigger('submit')
  expect(wrapper.emitted('apply')).toEqual([[['Sales']]])
})
