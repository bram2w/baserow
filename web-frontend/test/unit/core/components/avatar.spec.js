import { shallowMount } from '@vue/test-utils'
import Avatar from '@baserow/modules/core/components/Avatar'

describe('Avatar.vue', () => {
  it('renders the avatar with the correct classes when props are provided', () => {
    const rounded = true
    const color = 'green'
    const size = 'large'
    const wrapper = shallowMount(Avatar, {
      propsData: { rounded, color, size },
    })
    expect(wrapper.classes()).toContain('avatar')
    expect(wrapper.classes()).toContain('avatar--rounded')
    expect(wrapper.classes()).toContain(`avatar--${size}`)
    expect(wrapper.classes()).toContain(`avatar--${color}`)
  })

  it('renders the avatar with the image when the image prop is provided', () => {
    const image = 'https://example.com/image.jpg'
    const wrapper = shallowMount(Avatar, {
      propsData: { image },
    })
    expect(wrapper.find('.avatar__image').attributes('src')).toBe(image)
  })

  it('renders the avatar with the initials when the initials prop is provided', () => {
    const initials = 'JD'
    const wrapper = shallowMount(Avatar, {
      propsData: { initials },
    })
    expect(wrapper.find('.avatar__initials').text()).toBe(initials)
  })

  it('does not render the initials when the image prop is provided', () => {
    const image = 'https://example.com/image.jpg'
    const initials = 'JD'
    const wrapper = shallowMount(Avatar, {
      propsData: { image, initials },
    })
    expect(wrapper.find('.avatar__initials').exists()).toBe(false)
  })
})
