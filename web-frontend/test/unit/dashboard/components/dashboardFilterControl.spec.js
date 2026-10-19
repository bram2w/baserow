import { mount, flushPromises } from '@vue/test-utils'
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
let wrapper
afterEach(() => wrapper?.unmount())
function render({
  mode = 'dropdown',
  appliedValues = ['Design'],
  multiple = true,
  unavailable = [],
} = {}) {
  wrapper = mount(DashboardFilterControl, {
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
      mocks: { $t: (key) => key },
      directives: { tooltip: () => {} },
    },
  })
  return wrapper
}

test('discards unapplied dropdown changes on close and restores applied choices', async () => {
  render()
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
  render()
  await wrapper.get('.dashboard-filter__trigger').trigger('click')
  await wrapper.get('input[type="checkbox"]').setValue(false)
  expect(wrapper.emitted('apply')).toBeUndefined()
  await wrapper.get('form').trigger('submit')
  expect(wrapper.emitted('apply')).toEqual([[[]]])
  expect(wrapper.find('[data-testid="panel"]').exists()).toBe(false)
})

test('trims input on Apply and discards its unapplied edits', async () => {
  render({ mode: 'input', appliedValues: [] })
  await wrapper.get('.dashboard-filter__trigger').trigger('click')
  await wrapper.get('input').setValue('  Design  ')
  await wrapper.get('form').trigger('submit')
  expect(wrapper.emitted('apply')).toEqual([[['Design']]])
  await wrapper.get('.dashboard-filter__trigger').trigger('click')
  await flushPromises()
  expect(wrapper.get('input').element.value).toBe('')
})

test('shows unavailable selections and lets them be removed', async () => {
  render({ unavailable: ['Design'] })
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
