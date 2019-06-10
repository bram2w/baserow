import { mount } from '@vue/test-utils'
import Index from '@/pages/login/index.vue'

describe('Login', () => {
  test('is a Vue instance', () => {
    const wrapper = mount(Index)
    expect(wrapper.isVueInstance()).toBeTruthy()
  })
})
