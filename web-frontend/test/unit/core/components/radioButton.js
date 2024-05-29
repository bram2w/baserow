import { mount } from '@vue/test-utils'
import RadioButton from '@baserow/modules/core/components/RadioButton'

describe('RadioButton.vue', () => {
  it('renders the button', () => {
    const wrapper = mount(RadioButton)
    expect(wrapper.findComponent({ name: 'Button' }).exists()).toBe(true)
  })

  it('passes the correct props to the button', () => {
    const propsData = {
      loading: true,
      disabled: true,
      icon: 'test-icon',
      title: 'test-title',
    }
    const wrapper = mount(RadioButton, { propsData })

    const button = wrapper.findComponent({ name: 'Button' })
    Object.keys(propsData).forEach((key) => {
      expect(button.props(key)).toBe(propsData[key])
    })
  })

  it('emits input event with the correct value when the button is clicked', async () => {
    const value = 'test'
    const wrapper = mount(RadioButton, {
      propsData: {
        value,
      },
    })

    await wrapper.findComponent({ name: 'Button' }).trigger('click')

    expect(wrapper.emitted('input')[0]).toEqual([value])
  })
})
