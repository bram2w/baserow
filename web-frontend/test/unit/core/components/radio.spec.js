import { mount } from '@vue/test-utils'
import Radio from '@baserow/modules/core/components/Radio'

describe('Radio.vue', () => {
  it('renders the radio input', () => {
    const wrapper = mount(Radio)
    expect(wrapper.find('input[type="radio"]').exists()).toBe(true)
  })

  it('sets the correct value for the radio input', () => {
    const value = 'test'
    const wrapper = mount(Radio, {
      propsData: {
        value,
      },
    })

    expect(wrapper.find('input[type="radio"]').element.value).toBe(value)
  })

  it('sets the radio input as checked based on the modelValue prop', () => {
    const value = 'test'
    const wrapper = mount(Radio, {
      propsData: {
        value,
        modelValue: value,
      },
    })

    expect(wrapper.find('input[type="radio"]').element.checked).toBe(true)
  })

  it('disables the radio input based on the disabled prop', () => {
    const wrapper = mount(Radio, {
      propsData: {
        disabled: true,
      },
    })

    expect(wrapper.find('input[type="radio"]').element.disabled).toBe(true)
  })

  it('emits input event with the correct value when the radio input is clicked', async () => {
    const value = 'test'
    const wrapper = mount(Radio, {
      propsData: {
        value,
      },
    })

    await wrapper.find('input[type="radio"]').trigger('click')

    expect(wrapper.emitted('input')[0]).toEqual([value])
  })

  // Add more tests as needed...
})
