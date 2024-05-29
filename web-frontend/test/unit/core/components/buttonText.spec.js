import { shallowMount } from '@vue/test-utils'
import ButtonText from '@baserow/modules/core/components/ButtonText'

describe('ButtonText.vue', () => {
  it('renders the button text', () => {
    const text = 'Click me'
    const wrapper = shallowMount(ButtonText, {
      slots: {
        default: text,
      },
    })
    expect(wrapper.text()).toMatch(text)
  })

  it('renders an anchor tag when href prop is provided', () => {
    const href = 'https://example.com'
    const wrapper = shallowMount(ButtonText, {
      propsData: { href },
    })
    expect(wrapper.element.tagName).toBe('A')
  })

  it('emits the click event when clicked', () => {
    const wrapper = shallowMount(ButtonText)
    wrapper.vm.$emit('click')
    expect(wrapper.emitted().click).toBeTruthy()
  })

  it('disables the button when disabled prop is true', () => {
    const wrapper = shallowMount(ButtonText, {
      propsData: { disabled: true },
    })
    expect(wrapper.attributes('disabled')).toBe('disabled')
  })

  it('renders the button with the correct class when type prop is provided', () => {
    const type = 'secondary'
    const wrapper = shallowMount(ButtonText, {
      propsData: { type },
    })
    expect(wrapper.classes()).toContain(`button-text--${type}`)
  })

  it('renders the button with the correct size when size prop is provided', () => {
    const size = 'large'
    const wrapper = shallowMount(ButtonText, {
      propsData: { size },
    })
    expect(wrapper.classes()).toContain(`button-text--${size}`)
  })

  it('renders the button with the correct icon when icon prop is provided', () => {
    const icon = 'iconoir-plus'
    const wrapper = shallowMount(ButtonText, {
      propsData: { icon },
    })
    expect(wrapper.find('.button-text__icon').classes()).toContain(`${icon}`)
  })
})
