import { shallowMount } from '@vue/test-utils'
import RadioGroup from '@baserow/modules/core/components/RadioGroup'

describe('RadioGroup.vue', () => {
  it('renders the correct number of radio options', () => {
    const options = [
      { value: 'one', label: 'One' },
      { value: 'two', label: 'Two' },
      { value: 'three', label: 'Three' },
    ]
    const wrapper = shallowMount(RadioGroup, {
      propsData: {
        options,
      },
      global: {
        stubs: ['Radio'],
      },
    })

    const radios = wrapper.findAllComponents({ name: 'Radio' })
    expect(radios.length).toBe(options.length)
  })

  it('sets the correct radio option as selected based on the modelValue prop', () => {
    const options = [
      { value: 'one', label: 'One' },
      { value: 'two', label: 'Two' },
      { value: 'three', label: 'Three' },
    ]
    const modelValue = 'two'
    const wrapper = shallowMount(RadioGroup, {
      propsData: {
        options,
        modelValue,
      },
    })

    const selectedRadio = wrapper.findComponent({
      name: 'Radio',
      props: { modelValue },
    })
    expect(selectedRadio.exists()).toBe(true)
  })

  it('emits input event with the correct value when a radio option is selected', async () => {
    const options = [
      { value: 'one', label: 'One' },
      { value: 'two', label: 'Two' },
      { value: 'three', label: 'Three' },
    ]
    const wrapper = shallowMount(RadioGroup, {
      propsData: {
        options,
      },
    })

    const radioToSelect = wrapper.findComponent({
      name: 'Radio',
      props: { value: 'three' },
    })
    await radioToSelect.vm.$emit('input', 'three')

    expect(wrapper.emitted('input')[0]).toEqual(['three'])
  })

  it('updates the modelValue prop when a radio option is selected', async () => {
    const options = [
      { value: 'one', label: 'One' },
      { value: 'two', label: 'Two' },
      { value: 'three', label: 'Three' },
    ]
    const wrapper = shallowMount(RadioGroup, {
      propsData: {
        options,
        modelValue: 'one',
      },
    })

    const radioToSelect = wrapper.findComponent({
      name: 'Radio',
      props: { value: 'two' },
    })
    await radioToSelect.vm.$emit('input', 'two')

    expect(wrapper.emitted('input')[0]).toEqual(['two'])
  })
})
