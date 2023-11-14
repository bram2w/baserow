import { shallowMount } from '@vue/test-utils'
import Badge from '@baserow/modules/core/components/Badge'

describe('Badge.vue', () => {
  it('renders the badge with the correct color class when color prop is provided', () => {
    const color = 'green'
    const wrapper = shallowMount(Badge, {
      propsData: { color },
    })
    expect(wrapper.classes()).toContain(`badge--${color}`)
  })

  it('renders the badge with the correct size class when size prop is provided', () => {
    const size = 'small'
    const wrapper = shallowMount(Badge, {
      propsData: { size },
    })
    expect(wrapper.classes()).toContain(`badge--${size}`)
  })

  it('renders the badge with the rounded class when rounded prop is true', () => {
    const wrapper = shallowMount(Badge, {
      propsData: { rounded: true },
    })
    expect(wrapper.classes()).toContain('badge--rounded')
  })

  it('renders the badge with the indicator element when indicator prop is true', () => {
    const wrapper = shallowMount(Badge, {
      propsData: { indicator: true },
    })
    expect(wrapper.find('.badge__indicator').exists()).toBe(true)
  })

  it('renders the badge with the default color class when color prop is not provided', () => {
    const wrapper = shallowMount(Badge)
    expect(wrapper.classes()).toContain('badge--neutral')
  })

  it('renders the badge with the default size class when size prop is not provided', () => {
    const wrapper = shallowMount(Badge)
    expect(wrapper.classes()).toContain('badge--regular')
  })
})
