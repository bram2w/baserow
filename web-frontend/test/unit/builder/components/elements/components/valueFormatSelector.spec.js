import { mountSuspended } from '@nuxt/test-utils/runtime'
import ValueFormatSelector from '@baserow/modules/builder/components/elements/components/forms/ValueFormatSelector.vue'
import { MARKDOWN_PREFIX } from '@baserow/modules/core/formula/textFormat'

describe('ValueFormatSelector', () => {
  const mountComponent = (modelValue) =>
    mountSuspended(ValueFormatSelector, {
      props: { modelValue },
      mocks: { $t: (key) => key },
    })

  test('reads and writes the format of a formula object', async () => {
    const wrapper = await mountComponent({
      formula: "get('a')",
      mode: 'simple',
      version: '0.1',
    })
    const selector = wrapper.findComponent({ name: 'TextFormatSelector' })
    expect(selector.props('modelValue')).toBe('plain')

    await selector.vm.$emit('update:modelValue', 'markdown')

    expect(wrapper.emitted('update:modelValue')).toEqual([
      [
        {
          formula: `${MARKDOWN_PREFIX}get('a')`,
          mode: 'simple',
          version: '0.1',
        },
      ],
    ])
  })

  test('shows markdown for a marked formula and strips it on plain', async () => {
    const wrapper = await mountComponent({
      formula: `${MARKDOWN_PREFIX}get('a')`,
      mode: 'simple',
    })
    const selector = wrapper.findComponent({ name: 'TextFormatSelector' })
    expect(selector.props('modelValue')).toBe('markdown')

    await selector.vm.$emit('update:modelValue', 'plain')

    expect(wrapper.emitted('update:modelValue')).toEqual([
      [{ formula: "get('a')", mode: 'simple' }],
    ])
  })

  test('reads and writes the format of a plain string', async () => {
    const wrapper = await mountComponent('Name')
    const selector = wrapper.findComponent({ name: 'TextFormatSelector' })
    expect(selector.props('modelValue')).toBe('plain')

    await selector.vm.$emit('update:modelValue', 'markdown')

    expect(wrapper.emitted('update:modelValue')).toEqual([
      [`${MARKDOWN_PREFIX}Name`],
    ])
  })

  test('marks an empty formula object', async () => {
    const wrapper = await mountComponent({})
    const selector = wrapper.findComponent({ name: 'TextFormatSelector' })

    await selector.vm.$emit('update:modelValue', 'markdown')

    expect(wrapper.emitted('update:modelValue')).toEqual([
      [{ formula: MARKDOWN_PREFIX }],
    ])
  })
})
