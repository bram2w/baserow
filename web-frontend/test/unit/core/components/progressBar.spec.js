import { mount } from '@vue/test-utils'
import ProgressBar from '@baserow/modules/core/components/ProgressBar'

describe('ProgressBar.vue', () => {
  it('renders the progress bar', () => {
    const wrapper = mount(ProgressBar)
    expect(wrapper.find('.progress-bar').exists()).toBe(true)
  })

  it('sets the correct width based on the value prop', () => {
    const value = 72
    const wrapper = mount(ProgressBar, {
      propsData: {
        value,
      },
    })

    const progressBar = wrapper.find('.progress-bar__inner')
    expect(progressBar.attributes('style')).toContain(`width: ${value}%`)
  })

  it('shows the value when the showValue prop is true', () => {
    const value = 72
    const wrapper = mount(ProgressBar, {
      propsData: {
        value,
        showValue: true,
      },
    })

    expect(wrapper.text()).toContain(`${value}%`)
  })

  it('does not show the value when the showValue prop is false', () => {
    const value = 72
    const wrapper = mount(ProgressBar, {
      propsData: {
        value,
        showValue: false,
      },
    })

    expect(wrapper.text()).not.toContain(`${value}%`)
  })

  // Add more tests as needed...
})
