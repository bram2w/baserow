import { mount } from '@vue/test-utils'
import Signup from '@/pages/login/signup.vue'

describe('Signup', () => {
  test('is a Vue instance', () => {
    const wrapper = mount(Signup)
    expect(wrapper.isVueInstance()).toBeTruthy()
  })
})
