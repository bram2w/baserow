import { shallowMount } from '@vue/test-utils'
import Toast from '@baserow/modules/core/components/toasts/Toast'

describe('Toast.vue', () => {
  it('renders the toast with the correct type class when type prop is provided', () => {
    const type = 'success'
    const wrapper = shallowMount(Toast, {
      propsData: { type },
    })
    expect(wrapper.find('.toast__icon').classes()).toContain(
      `toast__icon--${type}`
    )
  })

  it('renders the toast title and message', () => {
    const title = 'This is an alert title.'
    const message = 'This is an alert message.'
    const wrapper = shallowMount(Toast, {
      slots: {
        title,
        default: message,
      },
    })
    expect(wrapper.find('.toast__title').text()).toMatch(title)
    expect(wrapper.find('.toast__message').text()).toMatch(message)
  })

  it('renders the toast with the actions slot when actions prop is provided', () => {
    const actionsSlot = '<button>OK</button>'
    const wrapper = shallowMount(Toast, {
      slots: {
        actions: actionsSlot,
      },
    })
    expect(wrapper.find('.toast__actions').html()).toContain(actionsSlot)
  })
  it('emits the close event when the close button is clicked', () => {
    const closeButton = true
    const wrapper = shallowMount(Toast, {
      propsData: { closeButton },
    })
    wrapper.find('.toast__close').trigger('click')
    expect(wrapper.emitted().close).toBeTruthy()
  })
})
